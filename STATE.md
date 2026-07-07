# STATE — Trạng thái dự án VidMak

> File sống, cập nhật cuối mỗi phiên làm việc. Đọc file này ĐẦU TIÊN khi bắt đầu session mới. Lịch sử cũ dồn xuống Session log, phần đầu luôn là hiện tại.

## Hiện tại

**Phase:** 1 đang chạy — orchestration chốt, tầng Analysis + Storyboard chạy được. Chờ user duyệt diff slice này.

**Git:** baseline commit `c6c6a51` trên `main` (đã push origin); nhánh `develop` đã tạo + push; đang làm trên `develop`. `Ref_Video.mp4` giữ ngoài repo (sửa `.gitignore`).

**Slice Phase 1 vừa xong (chờ duyệt):**
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

**Đang làm:** Chờ user xem diff (`git status`/danh sách file mới) và xác nhận trước khi `git commit` lần đầu.

**Tiếp theo (theo thứ tự):**
1. User duyệt diff slice Analysis + Storyboard → commit lên `develop`
2. Tầng 3 (Script): đọc `storyboard.json` sinh `script.json` — thoại tiếng Việt từng cảnh + ước lượng thời lượng đọc (schema ARCHITECTURE.md)
3. Tầng 4 (Codegen): sinh `scenes/*.py` dùng `manim_lib` + vòng tự sửa lỗi render (cầu nối tầng agent ↔ manim_lib; cần viết `components.py`/`solids.py` hiện thực các helper storyboard tham chiếu)

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

### 2026-07-08 — Định hình dự án
- Phân tích video tham chiếu, so sánh Manim vs hyperframes, user chốt dùng Manim
- Chốt pipeline 6 tầng: analysis → storyboard → script → manim codegen (tự sửa lỗi + QA thị giác) → TTS → assembly
- User yêu cầu UI tham khảo VideoDubbing (`apps/desktop/src/components/ui`) — đã port tokens vào DESIGN.md
- Viết toàn bộ tài liệu nền tảng của repo

### 2026-07-08 (tiếp) — Git baseline + Phase 1 khởi động
- Commit baseline lên `main` (`c6c6a51`, đã push), tạo nhánh `develop` (push), làm tiếp trên `develop`; `Ref_Video.mp4` giữ ngoài repo
- User cung cấp endpoint LLM local OpenAI-compatible (`cx/gpt-5.5`) → chốt D009 (plain Python + `openai` SDK, không framework); giải thích vì sao không dùng LangGraph/CrewAI
- Viết `pipeline/llm.py`, `workspace.py`, `agents/analysis.py`, `run.py`, `.env.example`; chạy thật ra `analysis.md` chất lượng cho topic "Khối tròn xoay"

### 2026-07-08 (tiếp) — Tầng 2 Storyboard
- Viết `pipeline/agents/storyboard.py` (tầng 2, đầu tư nhất): prompt sư phạm hình học 3B1B (một ý/cảnh, liên tục thị giác, trực giác trước công thức, ràng buộc 9:16 + safe-zone + Text/MathTex), menu helper ổn định, `validate()` + `_extract_json()`; nối vào `run.py`
- Chạy thật "Khối tròn xoay" → `storyboard.json` 9 cảnh liên tục thị giác, LaTeX chuẩn, đúng schema — sẵn sàng làm đầu vào tầng Script

### 2026-07-08 (tiếp) — Phase 0 hoàn tất
- Chốt workflow duyệt code: diff trước, commit sau khi user OK (không tự commit)
- `git init`, viết `.gitignore`
- Kiểm tra môi trường, phát hiện convention conda của các project khác → tạo env `vidmak` (Python 3.11), đổi quyết định venv→conda (D007)
- Gặp 2 sự cố cài đặt: DLL do trộn channel (fix bằng `--override-channels conda-forge`), và `manim-voiceover` 0.4.0 đã gỡ `EdgeTTSService` (fix bằng adapter tự viết) — cả hai ghi lại ở D008
- Render thành công `HelloScene`: tiêu đề + công thức tiếng Việt + voice đồng bộ, xác nhận bằng mắt qua frame trích xuất, khớp style Ref_Video.mp4
