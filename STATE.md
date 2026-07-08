# STATE — Trạng thái dự án VidMak

> File sống, cập nhật cuối mỗi phiên làm việc. Đọc file này ĐẦU TIÊN khi bắt đầu session mới. Lịch sử cũ dồn xuống Session log, phần đầu luôn là hiện tại.

## Hiện tại

**Phase:** 1 — 🎬 **TOÀN BỘ PIPELINE 6 TẦNG CHẠY THÔNG**: `run.py --topic` đi Analysis → Storyboard → Script → Codegen → Render → Assembly, ra `projects/khoi-tron-xoay/output/final.mp4` (720×1280@30, 105.9s, 9 cảnh có thoại). Chờ user duyệt diff slice 4b+4c.

**Git:** baseline `c6c6a51` (main, đã push); đang trên `develop`. Đã commit tới `5124236` (manim_lib 4a). `Ref_Video.mp4` ngoài repo.

**Slice 4b+4c vừa xong (chờ duyệt) — 3 file mới + 3 sửa:**
- `agents/codegen.py` (tầng 4b sinh): mỗi cảnh 1 LLM call → 1 `scenes/<id>.py` (VoiceoverScene, gọi manim_lib + EdgeTTSService). Prompt có API helper chính xác + ví dụ mẫu + 17 luật (Text/MathTex, safe-zone, add_fixed_in_frame cho 3D, cảnh nhẹ, cấm opacity0+FadeIn, **cấm stub voiceover**). `validate_scene_code` (ast + whitelist import + bắt stub voiceover), `repair_scene`, `fallback_scene_code`, NARRATION đóng đinh từ script.json.
- `render.py` (tầng 4b render): subprocess manim + `PYTHONPATH=manim_lib` (D010); vòng tự sửa ≤4 (kiểm tra tĩnh TRƯỚC mỗi render để không nhận bản cheat), quá 4 → fallback; **render song song** `workers` (D012, BLAS=1); `_find_output` theo quality.
- `assemble.py` (tầng 4c): ffmpeg concat filter 9 clip → `output/final.mp4`; chặn cảnh thiếu audio.
- `run.py`: nối [4/6] Codegen, [5/6] Render (`--workers`, `--draft`), [6/6] Assembly.
- `theme.py`: chế độ **draft** qua env `VIDMAK_DRAFT` (360×640@15); **sửa bug** thêm `config.frame_width=8.0` (D011).
- `DECISIONS.md`: D010 (flat import + PYTHONPATH), D011 (Cairo không OpenGL + draft + frame_width), D012 (render song song).

**Kết quả chạy thật topic "Khối tròn xoay" (9 cảnh, full-res Cairo, song song 7 worker, ~10 phút wall-clock):**
- 9/9 cảnh render sạch, 0 fallback; vòng tự sửa cứu s06/s07/s08 (1–3 vòng).
- Chạy **2 vòng QA thị giác** (tôi đóng vai vision model, trích frame): vòng 1 lộ 5 cảnh lỗi layout (chữ đè hình / mất chữ / end-card chồng); vòng 2 `repair_scene` với mô tả lỗi → sửa hết. Bắt thêm 2 bug sâu: s09 `set_opacity(0)+FadeIn` (end-card không hiện) và **s08 bị vòng self-repair "cheat" thay voiceover bằng stub câm → mất audio** (đã thêm luật 17 + validator + kiểm tra tĩnh trong repair loop, sinh lại s08 có audio).

**Đã commit:** `5124236` (manim_lib 4a), `c160daa` (Script), `d26049f` (Storyboard), `f87be04` (orchestration + Analysis), `c6c6a51` (baseline).

**Nền tảng Phase 1:**
- Chốt **D009** orchestration: plain Python + `openai` SDK trỏ proxy local `http://localhost:20128/v1`, model `cx/gpt-5.5` (đã test OK, trả tiếng Việt chuẩn). Không dùng LangGraph/CrewAI/Agent SDK. Cài `openai` 2.44.0 vào env `vidmak`
- `pipeline/llm.py` (client mỏng, config qua env var), `pipeline/workspace.py` (slug tiếng Việt → thư mục `projects/<slug>/`), `.env.example`
- `pipeline/agents/analysis.py` (tầng 1) + `pipeline/run.py` (CLI `--topic`)
- Chạy thật `--topic "Khối tròn xoay"` → `projects/khoi-tron-xoay/analysis.md`: cấu trúc đúng, LaTeX chuẩn, có mục "Hình ảnh hoá được" (6 cảnh) làm đầu vào cho tầng 2
- `pipeline/agents/storyboard.py` (tầng 2): prompt sư phạm hình học 3B1B + `validate()` cấu trúc + `_extract_json()` chịu lỗi fence; nối vào `run.py` (giờ `[1/2] Analysis → [2/2] Storyboard`)
- Chạy thật ra `storyboard.json`: 9 cảnh, id `s01..s09` tuần tự, liên tục thị giác (mỗi cảnh biến hình từ cảnh trước), trực giác trước công thức, chữ Việt ở `visual` / LaTeX ở `geometry_notes`, helpers bám menu cho phép. Lưu ý: tổng `duration_hint`=100s hơi vượt 90 (thoại mới là nguồn chân lý thời lượng — không chặn)

**Đã xong (Phase 0):**
- Phân tích Ref_Video.mp4 (22 frame): xác định style Manim/3Blue1Brown, cấu trúc cảnh, thông số 720×1280@30fps/87s
- Đánh giá hyperframes (HTML→video) và **loại** — chọn Manim (xem [DECISIONS.md](DECISIONS.md) D001)
- Chốt kiến trúc pipeline 6 tầng + tech stack (xem [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md))
- Khảo sát design system Aether Studio từ `D:\AgenticAI\VideoDubbing\apps\desktop` → chép tokens vào [DESIGN.md](DESIGN.md)
- Viết bộ tài liệu: PROJECT_OVERVIEW, PLAN, STATE, ARCHITECTURE, DESIGN, DECISIONS, CLAUDE.md
- `git init` + `.gitignore` (chưa commit — workflow là diff trước, commit sau khi duyệt, xem D007)
- Chốt workflow duyệt: tôi làm + show diff, chờ bạn OK rồi mới commit (không tự commit)
- **Phase 0 xong toàn bộ:**
  - Conda env `vidmak` (Python 3.11) tạo lại thuần conda-forge sau khi gặp lỗi DLL do trộn channel (D007, D008)
  - Cài `manim` 0.20.1, `manim-voiceover` 0.4.0, `edge-tts` 7.2.8
  - Viết `pipeline/manim_lib/theme.py` (config 9:16, bảng màu, font Cambria cho tiếng Việt)
  - Viết `pipeline/manim_lib/edge_tts_service.py` — adapter tự chế cho edge-tts (bản manim-voiceover mới đã gỡ `EdgeTTSService` tích hợp, xem D008)
  - Viết + render `pipeline/manim_lib/hello.py` (`HelloScene`): tiêu đề "Khối Tròn Xoay" (vàng) + `MathTex` công thức (cyan) + voice `vi-VN-HoaiMyNeural` đồng bộ — **đã kiểm tra bằng mắt qua frame trích xuất, khớp style Ref_Video.mp4**, có audio track AAC

**Đang làm:** Chờ user xem diff slice 4b+4c (3 file mới `codegen.py`/`render.py`/`assemble.py` + 3 sửa `theme.py`/`run.py`/`DECISIONS.md`) và xác nhận trước khi commit.

**Tiếp theo (theo thứ tự):**
1. User duyệt diff slice 4b+4c → commit lên `develop`
2. **Tầng QA thị giác tự động** (`qa/visual.py`, D004 vòng 2): hiện đang làm THỦ CÔNG (tôi trích frame + chấm mắt). Dữ liệu lỗi đã thu (chữ đè hình, mất chữ, end-card chồng, cảnh nặng) là spec để tự động hoá: ffmpeg trích 2 frame/cảnh → vision model chấm → `repair_scene` → re-render cảnh đó.
3. **Cache theo cảnh** (hash `scene.py` + narration) để rerun không tốn lại; hiện `_find_output` chỉ cache theo file mp4 tồn tại.
4. **Tinh chỉnh:** total_duration 105.9s hơi vượt 90 (siết `duration_hint`/số cảnh); glyph ✓/✗ thiếu trong Cambria (đổi ký hiệu); một số cảnh 3D hơi rối (s05 nhiều tia) — nới prompt.
5. Phase 2 lint (`qa/lint.py`): safe-zone tự động, thời lượng cảnh vs thoại; hiệu chỉnh `SPEECH_SYLLABLES_PER_SECOND` theo TTS thật.

## Blockers / câu hỏi mở

- [x] MiKTeX đã cài trên máy chưa? → **Có**, tại `C:\Users\phong\AppData\Local\Programs\MiKTeX\miktex\bin\x64\`
- [x] Orchestration: **plain Python + `openai` SDK trỏ proxy local `cx/gpt-5.5`**, không framework (D009)
- [ ] Chọn giọng mặc định: `vi-VN-HoaiMyNeural` (nữ) hay `vi-VN-NamMinhNeural` (nam)? — tạm mặc định nữ (đã dùng trong hello.py), cho chọn ở UI Phase 3
- [ ] Proxy tự chèn system prompt kiểu codex (~2500 token/call) — theo dõi xem có ảnh hưởng chất lượng tầng sau không; mỗi tầng đã đặt system prompt riêng để đè

## Môi trường máy dev (Windows 11)

| Thành phần | Trạng thái |
|---|---|
| FFmpeg | ✅ có sẵn (đã dùng để phân tích Ref_Video) |
| Python | ✅ 3.13.9 (Anaconda) trên PATH; conda env riêng `vidmak` dùng Python 3.11 |
| Conda | ✅ 26.1.1, env `vidmak` tạo thuần conda-forge (`--override-channels`) |
| MiKTeX (LaTeX) | ✅ có sẵn, `MathTex` render đúng |
| Node.js | ✅ v24.15.0 (cho Phase 3) |
| Manim | ✅ 0.20.1, render + voice xác nhận hoạt động |
| manim-voiceover / edge-tts | ✅ 0.4.0 / 7.2.8 — dùng qua adapter tự viết `edge_tts_service.py` |
| openai SDK | ✅ 2.44.0 — client cho proxy OpenAI-compatible local `cx/gpt-5.5` |
| LLM endpoint | ✅ `http://localhost:20128/v1` (proxy local, không kiểm key); backend `cx/*` cần auth codex còn hiệu lực |

## Session log

### 2026-07-08 (tiếp) — Tầng 4b+4c: pipeline chạy thông, ra final.mp4
- Viết `agents/codegen.py` (sinh scene theo từng cảnh, 17 luật, validate + repair + fallback, NARRATION đóng đinh), `render.py` (subprocess manim + PYTHONPATH manim_lib, vòng tự sửa ≤4 kiểm-tra-tĩnh-trước, render song song, draft mode), `assemble.py` (ffmpeg concat → final.mp4); nối `run.py` thành 6 tầng
- Vấn đề tốc độ: full-res Cairo cảnh 3D >20 phút. Thử GPU/OpenGL → nhanh (3 phút) nhưng fixed-frame chữ vỡ (giới hạn manim khung dọc, D011) → **ở lại Cairo**, bù bằng: cảnh nhẹ (prompt), draft mode (env), **render song song** (16 core, ~0.5GB/cảnh) → 9 cảnh ~10 phút. Nhân tiện sửa bug `frame_width` (D011)
- Chạy thật "Khối tròn xoay" → 9/9 cảnh sạch; 2 vòng QA thị giác thủ công sửa 5 lỗi layout; bắt+sửa 2 bug sâu (s09 opacity0+FadeIn, s08 self-repair cheat stub voiceover → mất audio, thêm guard)
- `final.mp4` 720×1280@30, 105.9s, 9 cảnh có thoại — **video hoàn chỉnh đầu tiên của dự án**. Ghi D010–D012

### 2026-07-08 — Định hình dự án
- Phân tích video tham chiếu, so sánh Manim vs hyperframes, user chốt dùng Manim
- Chốt pipeline 6 tầng: analysis → storyboard → script → manim codegen (tự sửa lỗi + QA thị giác) → TTS → assembly
- User yêu cầu UI tham khảo VideoDubbing (`apps/desktop/src/components/ui`) — đã port tokens vào DESIGN.md
- Viết toàn bộ tài liệu nền tảng của repo

### 2026-07-08 (tiếp) — Git baseline + Phase 1 khởi động
- Commit baseline lên `main` (`c6c6a51`, đã push), tạo nhánh `develop` (push), làm tiếp trên `develop`; `Ref_Video.mp4` giữ ngoài repo
- User cung cấp endpoint LLM local OpenAI-compatible (`cx/gpt-5.5`) → chốt D009 (plain Python + `openai` SDK, không framework); giải thích vì sao không dùng LangGraph/CrewAI
- Viết `pipeline/llm.py`, `workspace.py`, `agents/analysis.py`, `run.py`, `.env.example`; chạy thật ra `analysis.md` chất lượng cho topic "Khối tròn xoay"

### 2026-07-08 (tiếp) — Tầng 4a: thư viện manim_lib
- Hiện thực 10 helper storyboard/script tham chiếu: `components.py` (title_card, caption, formula_box, brace_label, end_card), `solids.py` (lathe_from_curve, disk_from_rect, cylinder_stack), `axes.py` (plane_2d, axes_3d) — tất cả bám `theme.py`
- Thêm module `axes.py` ngoài danh sách ARCHITECTURE (components/solids) do menu helper dùng namespace `axes.*`; solids dựng toạ độ thô 1:1 để khớp `axes_3d`
- `smoke.py` 2 scene gọi đủ 10 helper, render `-ql` OK cả 2, kiểm frame bằng mắt: màu/dấu tiếng Việt/khối tròn xoay đúng style 3B1B → thư viện sẵn sàng cho codegen (4b)

### 2026-07-08 (tiếp) — Tầng 3 Script
- Viết `pipeline/agents/script.py`: `storyboard.json` → `script.json`; prompt lời bình 3B1B (mạch liền nối cảnh, trực giác trước công thức, đọc công thức bằng lời không LaTeX thô, viết cho tai nghe/TTS), budget âm tiết mỗi cảnh theo `duration_hint`; `est_speech_seconds` tính bằng Python (đếm âm tiết / `SPEECH_SYLLABLES_PER_SECOND`) thay vì tin model; `validate()` chặn cứng id lệch storyboard; nối vào `run.py` thành `[3/3]`
- Chạy thật "Khối tròn xoay" → `script.json` 9 cảnh chất lượng, tổng est ≈ 98s — sẵn sàng làm đầu vào tầng Codegen

### 2026-07-08 (tiếp) — Tầng 2 Storyboard
- Viết `pipeline/agents/storyboard.py` (tầng 2, đầu tư nhất): prompt sư phạm hình học 3B1B (một ý/cảnh, liên tục thị giác, trực giác trước công thức, ràng buộc 9:16 + safe-zone + Text/MathTex), menu helper ổn định, `validate()` + `_extract_json()`; nối vào `run.py`
- Chạy thật "Khối tròn xoay" → `storyboard.json` 9 cảnh liên tục thị giác, LaTeX chuẩn, đúng schema — sẵn sàng làm đầu vào tầng Script

### 2026-07-08 (tiếp) — Phase 0 hoàn tất
- Chốt workflow duyệt code: diff trước, commit sau khi user OK (không tự commit)
- `git init`, viết `.gitignore`
- Kiểm tra môi trường, phát hiện convention conda của các project khác → tạo env `vidmak` (Python 3.11), đổi quyết định venv→conda (D007)
- Gặp 2 sự cố cài đặt: DLL do trộn channel (fix bằng `--override-channels conda-forge`), và `manim-voiceover` 0.4.0 đã gỡ `EdgeTTSService` (fix bằng adapter tự viết) — cả hai ghi lại ở D008
- Render thành công `HelloScene`: tiêu đề + công thức tiếng Việt + voice đồng bộ, xác nhận bằng mắt qua frame trích xuất, khớp style Ref_Video.mp4
