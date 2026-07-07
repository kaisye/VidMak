# ARCHITECTURE — Kiến trúc kỹ thuật VidMak

## Cấu trúc thư mục (mục tiêu)

```
VidMak/
├── CLAUDE.md  PLAN.md  STATE.md  PROJECT_OVERVIEW.md  DESIGN.md  DECISIONS.md
├── pipeline/                  # Python — lõi agentic
│   ├── run.py                 # entrypoint: --topic "..." [--duration 90] [--voice ...]
│   ├── agents/                # mỗi tầng 1 module: prompt + runner + validator
│   │   ├── analysis.py
│   │   ├── storyboard.py
│   │   ├── script.py
│   │   └── codegen.py         # gồm cả vòng lặp tự sửa lỗi render
│   ├── manim_lib/             # thư viện Manim dùng chung (agent GỌI, không tự viết lại)
│   │   ├── theme.py           # config 9:16, bảng màu, font (DESIGN.md mục B)
│   │   ├── edge_tts_service.py # adapter SpeechService cho edge-tts (D008 — bản mới của
│   │   │                      # manim-voiceover không còn EdgeTTSService tích hợp sẵn)
│   │   ├── hello.py           # scene kiểm tra toolchain Phase 0 (không thuộc pipeline sinh video)
│   │   ├── components.py      # banner, end-card, brace chú thích, khung công thức (Phase 1)
│   │   └── solids.py          # helper 3D hay dùng (lathe từ f(x), xếp lát trụ, ...) (Phase 1)
│   ├── qa/
│   │   ├── visual.py          # trích frame → vision model → báo cáo lỗi layout
│   │   └── lint.py            # safe-zone, thời lượng cảnh vs thoại
│   └── render.py              # gọi manim CLI, parse stderr, quản lý cache theo cảnh
├── projects/                  # OUTPUT — mỗi topic một thư mục, gitignore media
│   └── <topic-slug>/
│       ├── analysis.md
│       ├── storyboard.json
│       ├── script.json
│       ├── scenes/            # *.py do agent sinh
│       ├── media/             # manim output trung gian (gitignore)
│       └── output/final.mp4
├── apps/desktop/              # Phase 3 — Tauri + React UI
└── Ref_Video.mp4              # video chuẩn chất lượng
```

## Data contracts giữa các tầng

Mỗi tầng chỉ đọc artifact của tầng trước, ghi artifact của mình. Không tầng nào gọi thẳng tầng khác — cho phép chạy lại từng tầng độc lập.

### `storyboard.json`

```json
{
  "topic": "Khối tròn xoay",
  "audience": "lớp 12",
  "total_duration_target": 90,
  "banner": { "text": "Khai giảng khoá ...", "enabled": true },
  "scenes": [
    {
      "id": "s01_title",
      "visual": "Tiêu đề 'Khối Tròn Xoay' vàng, công thức V=π∫ viết dần bên dưới",
      "geometry_notes": "MathTex reveal từng ký tự",
      "duration_hint": 8,
      "helpers": ["components.title_card"]
    },
    {
      "id": "s04_rotate",
      "visual": "Hình chữ nhật vàng quay quanh Ox thành lát trụ, camera chuyển 3D",
      "geometry_notes": "ThreeDScene, solids.disk_from_rect",
      "duration_hint": 12,
      "helpers": ["solids.disk_from_rect"]
    }
  ],
  "endcard": { "lines": ["KHOÁ ÔN TẬP KIẾN THỨC LỚP 11", "MIỄN PHÍ", "..."] }
}
```

### `script.json`

```json
{
  "scenes": [
    {
      "id": "s04_rotate",
      "narration": "Bây giờ, hãy quay hình chữ nhật này quanh trục Ox...",
      "est_speech_seconds": 6.5,
      "onscreen_text": "Quay hình chữ nhật này quanh trục Ox..."
    }
  ]
}
```

Quy tắc: `narration` là nguồn chân lý về thời lượng — codegen dùng `manim-voiceover` tracker để animation co giãn theo thoại, `duration_hint` chỉ để ước lượng tổng.

## Tầng 4 — Codegen: hai vòng lặp chất lượng

```
sinh scenes/*.py
      │
      ▼
┌─ VÒNG 1: SỬA LỖI RENDER (bắt buộc pass) ─────────────┐
│  manim render -ql → exit code ≠ 0?                    │
│  → parse stderr → đưa (code + lỗi) lại agent → sửa    │
│  → retry, tối đa 4 vòng; quá 4: đơn giản hoá scene    │
└──────────────────────┬────────────────────────────────┘
                       ▼
┌─ VÒNG 2: QA THỊ GIÁC (bắt buộc pass) ────────────────┐
│  ffmpeg trích 2 frame/cảnh → vision model kiểm:       │
│  chữ đè nhau / tràn khung / ngoài safe-zone / tương   │
│  phản kém → agent sửa layout → re-render CẢNH đó      │
└──────────────────────┬────────────────────────────────┘
                       ▼
            render -qh bản cuối → assembly
```

Nguyên tắc render: `-ql` (480p15) trong mọi vòng lặp, `-qh` (1080p... theo config 720×1280@30) chỉ một lần cuối. Cache theo cảnh: hash(scene .py + script narration) → bỏ qua cảnh không đổi.

## Voice (tầng 5)

- `manim-voiceover` + `EdgeTTSService`, giọng mặc định `vi-VN-HoaiMyNeural`
- Pattern trong scene:
  ```python
  with self.voiceover(text=narration) as tracker:
      self.play(..., run_time=tracker.duration)
  ```
- TTS được cache bởi manim-voiceover (hash theo text) — đổi thoại mới tốn gọi lại

## Quy ước Manim quan trọng

- **`Text()` cho mọi chữ tiếng Việt** (Pango render dấu chuẩn); **`MathTex()` chỉ cho công thức** — cấm trộn tiếng Việt có dấu vào LaTeX
- Mọi scene import `manim_lib.theme` — không hardcode màu/kích thước
- Config 9:16: `pixel_width=720, pixel_height=1280, frame_width=8.0, frame_height=14.22`
- Safe-zone: chừa 1.2 unit trên (banner) và 1.0 unit dưới (UI platform che)
- Mỗi cảnh là một class Scene riêng, ghép ở assembly — không nhét cả video vào 1 Scene

## Orchestration

Phase 1 chạy pipeline bằng Python + Claude API (model mặc định: `claude-sonnet-5` cho tầng 1–3, codegen và QA thị giác dùng model mạnh hơn nếu cần). Chi tiết chốt ở đầu Phase 1 — xem [DECISIONS.md](DECISIONS.md) D003. UI Phase 3 gọi pipeline qua Tauri sidecar.
