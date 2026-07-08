# PLAN — Kế hoạch triển khai VidMak

> Nguyên tắc: mỗi phase kết thúc bằng một deliverable **chạy được và kiểm chứng được**. Không sang phase sau khi acceptance của phase trước chưa đạt. Cập nhật tiến độ vào [STATE.md](STATE.md), không sửa lịch sử ở đây.

## Phase 0 — Môi trường & style foundation ✅ (2026-07-08)

**Mục tiêu:** máy render được 1 scene Manim tiếng Việt có voice, đúng style video tham chiếu.

- [x] Conda env `vidmak` (Python 3.11, thuần conda-forge) + `manim` 0.20.1, `manim-voiceover` 0.4.0, `edge-tts` 7.2.8 (đổi từ venv sang conda — D007; xử lý 2 sự cố cài đặt — D008)
- [x] Kiểm tra LaTeX (MiKTeX có sẵn); FFmpeg có sẵn
- [x] Module `pipeline/manim_lib/theme.py`: config 9:16 (pixel 720×1280, frame height 14.22 → width 8.0 tự suy ra), bảng màu, font Cambria cho tiếng Việt (theo [DESIGN.md](DESIGN.md) mục B) — banner/end-card helper để dành cho Phase 1 (`components.py`)
- [x] `pipeline/manim_lib/edge_tts_service.py`: adapter SpeechService tự viết cho edge-tts (built-in bị gỡ ở manim-voiceover 0.4.0)
- [x] Scene "hello world" (`pipeline/manim_lib/hello.py`): tiêu đề tiếng Việt + `MathTex` + voice edge-tts đồng bộ qua `tracker.duration`

**Acceptance: ĐẠT.** MP4 720×1280@30fps, chữ Việt "Khối Tròn Xoay" hiển thị đúng dấu (Pango), công thức `MathTex` đúng màu, có audio track AAC (giọng `vi-VN-HoaiMyNeural`) khớp animation, tông màu khớp Ref_Video.mp4 (nền đen, tiêu đề vàng, công thức cyan).

## Phase 1 — MVP pipeline end-to-end (CLI)

**Mục tiêu:** `python pipeline/run.py --topic "Khối tròn xoay"` ra `final.mp4` không cần can thiệp tay.

- [x] Orchestration: chốt D009 (plain Python + `openai` SDK trỏ proxy local `cx/gpt-5.5`, không framework); `pipeline/llm.py` + `workspace.py` + `run.py`
- [x] Định nghĩa schema artifact: `analysis.md`, `storyboard.json`, `script.json` (xem [ARCHITECTURE.md](ARCHITECTURE.md)) — cả 3 đã có validator + chạy thật ra artifact đúng schema
- [x] Agent tầng 1 (Analysis): prompt + runner — chạy được, ra `analysis.md` tiếng Việt có mục "Hình ảnh hoá được" cho tầng 2
- [x] Agent tầng 2 (Storyboard): prompt chuyên sâu sư phạm hình học — **đầu tư nhiều nhất ở đây**. Ra `storyboard.json` (schema ARCHITECTURE.md) có validator; test "Khối tròn xoay" → 9 cảnh liên tục thị giác, trực giác trước công thức
- [x] Agent tầng 3 (Script): thoại tiếng Việt theo cảnh, ước lượng thời lượng đọc — `script.json` (narration + onscreen_text + est_speech_seconds tính bằng Python), validator chặn id lệch storyboard; test "Khối tròn xoay" → 9 cảnh mạch liền, tổng est ≈ 98s
- [x] Agent tầng 4 (Codegen): `agents/codegen.py` sinh `scenes/<id>.py` (VoiceoverScene) dùng `manim_lib` + `edge_tts_service`; prompt 17 luật + API helper + validator (ast/whitelist/anti-stub); flat import + PYTHONPATH (D010)
- [x] **Vòng lặp tự sửa lỗi render:** `render.py` chạy manim (subprocess) → bắt stderr/kiểm-tra-tĩnh → `repair_scene` → retry ≤4, quá thì fallback tối giản; render song song `workers` (D012); draft mode (D011)
- [x] Ghép cảnh thành `output/final.mp4`: `assemble.py` (ffmpeg concat filter, chặn cảnh mất audio); nối `run.py` [6/6]

**Acceptance:** topic "Khối tròn xoay" ra video hoàn chỉnh có voice, so sánh được với Ref_Video.mp4; chạy lại với 1 topic khác (vd "Đạo hàm là gì") không sửa code.
> ✅ Nửa đầu ĐẠT: "Khối tròn xoay" → `final.mp4` 720×1280@30, 105.9s, 9 cảnh có thoại (2026-07-08). Chưa kiểm điều kiện "topic khác không sửa code" và "so sánh Ref_Video" (làm ở Phase 2). QA thị giác hiện thủ công — tự động hoá ở Phase 2.

## Phase 2 — Hardening & chất lượng

**Mục tiêu:** video ra "đăng được luôn", pipeline chịu lỗi tốt.

- [ ] **QA thị giác:** trích 1–2 frame/cảnh → vision model chấm (chữ đè nhau, tràn khung, tương phản) → agent sửa layout → re-render cảnh lỗi (không re-render cả video)
- [ ] Cache TTS + render theo cảnh (chỉ render lại cảnh thay đổi)
- [ ] Retry policy, timeout, log có cấu trúc cho từng tầng
- [ ] Lint tự động: text ngoài safe-zone 9:16, thời lượng cảnh lệch quá X% so với thoại
- [ ] Bộ topic regression (3–5 topic) chạy smoke test

**Acceptance:** 3 topic khác nhau đều ra video đạt, không có lỗi layout nhìn thấy được.

## Phase 3 — Desktop UI (Tauri + React)

**Mục tiêu:** người dùng không cần terminal. UI theo design system Aether Studio (xem [DESIGN.md](DESIGN.md) mục A).

- [ ] Scaffold Tauri + React + Tailwind v4, port `styles.css` tokens + thư mục `components/ui/` từ VideoDubbing
- [ ] Màn hình Create: nhập topic, tuỳ chọn (thời lượng, cấp độ, giọng đọc, banner/CTA text)
- [ ] Màn hình Progress: steplist 6 tầng (pattern `.steplist` của VideoDubbing), log box, progress bar
- [ ] Màn hình Result: VideoPreview + nút mở thư mục / re-render cảnh
- [ ] Màn hình History: danh sách project đã tạo (pattern `.joblist`/`.pill`)
- [ ] UI gọi pipeline Python qua Tauri sidecar hoặc local server

**Acceptance:** tạo video hoàn chỉnh chỉ bằng UI, theo dõi được tiến độ từng tầng.

## Phase 4 — Mở rộng (backlog, chưa cam kết)

- Thư viện template (banner, end-card, intro) cấu hình được
- Nhiều tỉ lệ khung hình (16:9 bài giảng dài, 1:1)
- Batch mode: danh sách topic → hàng loạt video
- Giọng đọc tuỳ chọn nâng cao (ElevenLabs), nhạc nền
- Preset theo môn học (Toán / Lý / Hoá)

## Rủi ro chính & đối sách

| Rủi ro | Đối sách |
|---|---|
| Code Manim do LLM sinh lỗi nhiều vòng không hội tụ | Giới hạn scene phức tạp, thư viện helper trong `manim_lib/` để agent gọi thay vì tự viết từ đầu |
| Layout xấu dù code chạy | QA thị giác bằng vision model (Phase 2) là bắt buộc, không phải tuỳ chọn |
| Storyboard nông, video đúng nhưng nhạt | Tách tầng 2 thành agent riêng với prompt sư phạm chuyên sâu + ví dụ few-shot từ Ref_Video |
| Tiếng Việt vỡ dấu trong LaTeX | Quy ước cứng: `Text()` (Pango) cho lời văn, `MathTex()` chỉ cho công thức |
| Render chậm khi lặp sửa lỗi | Render preview `-ql` trong vòng lặp, chỉ render `-qh` bản cuối |
