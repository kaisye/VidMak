# VidMak — Tổng quan dự án

> **Một câu:** Nhập topic học thuật → hệ thống agentic AI tự phân tích, thiết kế lời giải thích bằng hình học trực quan, viết kịch bản, render video Manim kiểu 3Blue1Brown kèm giọng thuyết minh tiếng Việt — ra file MP4 hoàn chỉnh.

## Bài toán

Tạo video giáo dục dạng short (9:16) chất lượng cao hiện tốn nhiều công: nghiên cứu nội dung, nghĩ cách trực quan hoá, viết kịch bản, code animation, thu âm, dựng phim. VidMak tự động hoá toàn bộ chuỗi này bằng một pipeline nhiều agent, mỗi agent đảm nhiệm một tầng chuyên môn.

## Video tham chiếu

[Ref_Video.mp4](Ref_Video.mp4) — video mẫu về "Khối Tròn Xoay" (87s, 720×1280@30fps, phong cách 3Blue1Brown/Manim):
- Nền đen, công thức LaTeX vàng/trắng, đồ thị cyan, highlight vàng
- Trình tự sư phạm: công thức → trục toạ độ 2D → chia lát Riemann → quay quanh Ox thành lát trụ 3D → xếp chồng dx→0 → công thức tổng quát → end-card CTA
- Banner cố định trên đầu (quảng bá khoá học), end-card khung viền vàng

Đây là "chuẩn chất lượng" mà pipeline phải đạt được.

## Pipeline (6 tầng)

```
Topic ──▶ [1] Phân tích học thuật ──▶ [2] Storyboard hình học ──▶ [3] Kịch bản thuyết minh
                                                                          │
Final MP4 ◀── [6] Assembly ◀── [5] TTS (trong Manim) ◀── [4] Sinh code Manim + tự sửa lỗi
```

| Tầng | Nhiệm vụ | Artifact |
|---|---|---|
| 1. Analysis | Khái niệm cốt lõi, cấp độ người học, insight trực quan chính | `analysis.md` |
| 2. Storyboard | Trình tự cảnh hình học (điểm ăn tiền về sư phạm) | `storyboard.json` |
| 3. Script | Lời thuyết minh tiếng Việt khớp từng cảnh | `script.json` |
| 4. Manim codegen | Sinh `scenes/*.py`, render, vòng lặp tự sửa lỗi + QA thị giác | `scenes/*.py` |
| 5. Voice | TTS tiếng Việt qua manim-voiceover (đồng bộ animation theo thoại) | audio cache |
| 6. Assembly | Ghép cảnh, banner, end-card | `output/final.mp4` |

## Tech stack

| Thành phần | Lựa chọn | Lý do |
|---|---|---|
| Animation engine | **Manim Community Edition** (Python) | Chuẩn 3Blue1Brown, khớp video tham chiếu |
| Voice sync | **manim-voiceover** + **edge-tts** (`vi-VN-HoaiMyNeural`/`NamMinhNeural`) | Animation tự co giãn theo thoại, TTS miễn phí giọng Việt tốt |
| Orchestration | Claude Agent SDK / Claude Code (Python pipeline, artifact JSON giữa các tầng) | Vòng lặp tự sửa lỗi cần môi trường agentic |
| Desktop UI | **Tauri + React + Tailwind v4**, tái dùng design tokens Aether Studio từ `D:\AgenticAI\VideoDubbing` | Đồng bộ hệ sinh thái, xem [DESIGN.md](DESIGN.md) |
| Output | MP4 9:16, 720×1280@30fps, 60–90s | Chuẩn short-form |

## Trạng thái & tài liệu

- [STATE.md](STATE.md) — trạng thái hiện tại, việc tiếp theo (**đọc đầu mỗi session**)
- [PLAN.md](PLAN.md) — kế hoạch theo phase
- [ARCHITECTURE.md](ARCHITECTURE.md) — kiến trúc chi tiết, data contracts, cấu trúc thư mục
- [DESIGN.md](DESIGN.md) — design system UI (app) + style guide video (Manim)
- [DECISIONS.md](DECISIONS.md) — nhật ký quyết định kỹ thuật (ADR)
- [CLAUDE.md](CLAUDE.md) — quy ước làm việc cho AI agent trong repo này
