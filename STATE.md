# STATE — Trạng thái dự án VidMak

> File sống, cập nhật cuối mỗi phiên làm việc. Đọc file này ĐẦU TIÊN khi bắt đầu session mới. Lịch sử cũ dồn xuống Session log, phần đầu luôn là hiện tại.

## Hiện tại

**Phase:** 0 hoàn tất ✅ — chờ user duyệt diff trước khi commit, sau đó chuyển sang Phase 1.

**Đã xong:**
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

**Đang làm:** Chờ user xem diff (`git status`/danh sách file mới) và xác nhận trước khi `git commit` lần đầu.

**Tiếp theo (theo thứ tự):**
1. User duyệt diff → commit baseline (docs + Phase 0 code)
2. Bắt đầu Phase 1: định nghĩa schema artifact cụ thể, viết agent tầng 1 (Analysis)
3. Đầu Phase 1: chốt câu hỏi mở "Orchestration" bên dưới

## Blockers / câu hỏi mở

- [x] MiKTeX đã cài trên máy chưa? → **Có**, tại `C:\Users\phong\AppData\Local\Programs\MiKTeX\miktex\bin\x64\`
- [ ] Chọn giọng mặc định: `vi-VN-HoaiMyNeural` (nữ) hay `vi-VN-NamMinhNeural` (nam)? — tạm mặc định nữ (đã dùng trong hello.py), cho chọn ở UI Phase 3
- [ ] Orchestration cụ thể: script Python gọi Claude API trực tiếp hay Claude Agent SDK? — quyết ở đầu Phase 1 (xem D003)

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

## Session log

### 2026-07-08 — Định hình dự án
- Phân tích video tham chiếu, so sánh Manim vs hyperframes, user chốt dùng Manim
- Chốt pipeline 6 tầng: analysis → storyboard → script → manim codegen (tự sửa lỗi + QA thị giác) → TTS → assembly
- User yêu cầu UI tham khảo VideoDubbing (`apps/desktop/src/components/ui`) — đã port tokens vào DESIGN.md
- Viết toàn bộ tài liệu nền tảng của repo

### 2026-07-08 (tiếp) — Phase 0 hoàn tất
- Chốt workflow duyệt code: diff trước, commit sau khi user OK (không tự commit)
- `git init`, viết `.gitignore`
- Kiểm tra môi trường, phát hiện convention conda của các project khác → tạo env `vidmak` (Python 3.11), đổi quyết định venv→conda (D007)
- Gặp 2 sự cố cài đặt: DLL do trộn channel (fix bằng `--override-channels conda-forge`), và `manim-voiceover` 0.4.0 đã gỡ `EdgeTTSService` (fix bằng adapter tự viết) — cả hai ghi lại ở D008
- Render thành công `HelloScene`: tiêu đề + công thức tiếng Việt + voice đồng bộ, xác nhận bằng mắt qua frame trích xuất, khớp style Ref_Video.mp4
