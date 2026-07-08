# STATE — Trạng thái dự án VidMak

> File sống, cập nhật cuối mỗi phiên làm việc. Đọc file này ĐẦU TIÊN khi bắt đầu session mới. Lịch sử cũ dồn xuống Session log, phần đầu luôn là hiện tại.

## Hiện tại

**Phase:** 1 đang chạy — orchestration chốt; tầng Analysis + Storyboard + Script chạy được; thư viện `manim_lib` (10 helper cho tầng 4) đã hiện thực + render smoke test đạt. Chờ user duyệt diff slice 4a.

**Git:** baseline commit `c6c6a51` trên `main` (đã push origin); nhánh `develop` đã tạo + push; đang làm trên `develop`. `Ref_Video.mp4` giữ ngoài repo (sửa `.gitignore`).

**Slice 4a (manim_lib helpers) vừa xong (chờ duyệt):**
- Hiện thực 10 helper mà storyboard/script tham chiếu, tất cả import `theme.py` (không hardcode màu):
  - `manim_lib/components.py`: `title_card`, `caption`, `formula_box`, `brace_label`, `end_card` (overlay 2D)
  - `manim_lib/solids.py`: `lathe_from_curve` (mặt tròn xoay quanh Ox), `disk_from_rect` (1 đĩa mỏng), `cylinder_stack` (chồng đĩa Riemann) — dựng ở toạ độ thô 1:1
  - `manim_lib/axes.py`: `plane_2d` (Ox đỏ/Oy xanh lá), `axes_3d` (map 1:1 khớp solids) — **module mới ngoài 2 module ARCHITECTURE liệt kê**, vì menu helper dùng namespace `axes.*`
- `manim_lib/smoke.py` (không thuộc pipeline sinh video): 2 scene `ComponentsSmoke` + `SolidsSmoke` gọi đủ 10 helper. Render `-ql` (media ra thư mục tạm) → **cả 2 MP4 sinh ra, 0 traceback**; trích frame kiểm mắt: tiêu đề gold đúng dấu, brace/formula/end-card chuẩn, mặt tròn xoay + chồng đĩa cyan-checkerboard viền gold đúng chất 3B1B. Xác nhận `configure()` áp đúng 720×1280@30 ngay ở `-ql`

**Đã commit:** `d26049f` (Storyboard), `f87be04` (orchestration + Analysis), + slice Script (tầng 3).

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

**Đang làm:** Chờ user xem diff slice 4a (4 file mới trong `manim_lib/`) và xác nhận trước khi commit.

**Tiếp theo (theo thứ tự):**
1. User duyệt diff slice 4a → commit lên `develop`
2. **Tầng 4b (Codegen agent):** `agents/codegen.py` sinh `projects/<slug>/scenes/*.py` từ storyboard + script, mỗi cảnh một `VoiceoverScene` gọi helper `manim_lib` + `EdgeTTSService`. Cần quyết định cách generated scene import `manim_lib` (package vs bơm PYTHONPATH trong `render.py`)
3. **Tầng 4b (Render self-repair):** `render.py` chạy manim `-ql` → bắt stderr → đưa lỗi lại model sửa → retry ≤4 vòng
4. **Tầng 4c (Assembly):** ghép `scenes/*` → `output/final.mp4`

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
