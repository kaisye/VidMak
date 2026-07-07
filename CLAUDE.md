# CLAUDE.md — Quy ước làm việc trong repo VidMak

VidMak: pipeline agentic AI biến topic học thuật thành video Manim kiểu 3Blue1Brown có thuyết minh tiếng Việt (short 9:16). Chi tiết: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md).

## Bắt đầu mỗi session

1. **Đọc [STATE.md](STATE.md) trước tiên** — trạng thái hiện tại, việc tiếp theo, blockers
2. Việc lớn hơn 1 bước: đối chiếu [PLAN.md](PLAN.md) đang ở phase nào
3. Trước khi ra quyết định kỹ thuật mới: xem [DECISIONS.md](DECISIONS.md) để không đảo ngược quyết định cũ mà không ghi lại

## Kết thúc mỗi session

- Cập nhật STATE.md: mục "Hiện tại" + thêm dòng vào Session log (ngày + tóm tắt)
- Quyết định kỹ thuật mới → thêm mục Dxxx vào DECISIONS.md
- Tick các mục hoàn thành trong PLAN.md (không sửa nội dung phase đã chốt)

## Bản đồ tài liệu

| File | Nội dung | Khi nào đụng tới |
|---|---|---|
| STATE.md | Trạng thái sống | Đầu + cuối mọi session |
| PLAN.md | Kế hoạch phase, acceptance | Bắt đầu/kết thúc hạng mục |
| ARCHITECTURE.md | Cấu trúc thư mục, schema artifact, vòng lặp chất lượng | Viết code pipeline |
| DESIGN.md | A: UI tokens (từ VideoDubbing) / B: style video Manim | Viết UI hoặc scene Manim |
| DECISIONS.md | ADR log | Trước quyết định mới |

## Quy ước code

### Manim (pipeline/)
- Mọi scene **import `manim_lib.theme`** — cấm hardcode màu, kích thước khung
- **`Text()` cho tiếng Việt, `MathTex()` chỉ cho công thức** — không trộn tiếng Việt có dấu vào LaTeX
- Render lặp/dev dùng `-ql`; chỉ render chất lượng cao một lần cuối
- Mỗi cảnh một class Scene; thoại qua `manim-voiceover` với `tracker.duration`
- Artifact sinh ra để trong `projects/<slug>/`, không lẫn vào `pipeline/`

### UI (apps/desktop/, Phase 3)
- Port design tokens + components từ `D:\AgenticAI\VideoDubbing\apps\desktop\src` — không tự chế component mới nếu inventory trong DESIGN.md mục A đã có
- Style bằng CSS variables (`var(--primary)`...), không hardcode màu

### Chung
- Ngôn ngữ: tài liệu + text hướng người dùng bằng tiếng Việt; tên biến/hàm/commit bằng tiếng Anh
- Commit nhỏ theo hạng mục; không commit `projects/*/media/`, venv, `node_modules` (giữ `.gitignore` đúng)
- Không commit API key; key đọc từ biến môi trường

## Môi trường

- Windows 11, shell PowerShell/Bash; FFmpeg và MiKTeX có sẵn trên PATH
- **Conda env tên `vidmak`** (Python 3.11) — theo đúng convention các project khác trong `D:\AgenticAI\` (aether-diarization, keeptrack, omnivoice đều dùng conda, không dùng venv)
- Cài Manim qua **conda-forge** (không dùng pip trực tiếp) để tránh lỗi build `pycairo`/`pangocairocffi` trên Windows
- Kiểm tra hiện trạng công cụ trong bảng ở STATE.md trước khi cài mới

## Lệnh thường dùng (cập nhật dần khi code hình thành)

```powershell
# Kích hoạt env
conda activate vidmak

# Render 1 scene preview (Phase 0+)
manim render -ql pipeline\manim_lib\hello.py HelloScene

# Chạy pipeline (Phase 1+)
python pipeline\run.py --topic "Khối tròn xoay"
```
