# DECISIONS — Nhật ký quyết định kỹ thuật (ADR-lite)

> Mỗi quyết định quan trọng ghi một mục: bối cảnh → quyết định → lý do → hệ quả. Không xoá mục cũ; nếu đảo ngược, thêm mục mới trỏ về mục bị thay thế.

---

## D001 — Dùng Manim, không dùng hyperframes/Remotion (2026-07-08)

**Bối cảnh:** Video tham chiếu Ref_Video.mp4 mang chữ ký thị giác Manim (nền đen, LaTeX Computer Modern, surface checkerboard). Đã đánh giá hyperframes (HeyGen, HTML→video qua Puppeteer+FFmpeg) — khả thi nhưng phải tự dựng lại toàn bộ ngôn ngữ hình học toán (trục, brace, lathe 3D...) bằng SVG/Three.js.

**Quyết định:** Manim Community Edition làm engine duy nhất.

**Lý do:** Khớp 1:1 với chuẩn chất lượng; hệ sinh thái toán học có sẵn (MathTex, ThreeDScene, Brace, Surface); cộng đồng lớn nên LLM sinh code Manim tốt hơn hẳn sinh Three.js tự chế.

**Hệ quả:** Cần LaTeX (MiKTeX) trên máy; render chậm hơn HTML capture; đường UI web-preview khó hơn (chấp nhận — output là file MP4).

## D002 — Voice: manim-voiceover + edge-tts (2026-07-08)

**Quyết định:** Đồng bộ thoại-animation bằng plugin `manim-voiceover` (pattern `tracker.duration`), TTS mặc định `edge-tts` giọng `vi-VN-HoaiMyNeural`.

**Lý do:** Giải quyết tận gốc bài toán sync (animation co giãn theo thoại thay vì ghép audio hậu kỳ — nguồn lệch lớn nhất); edge-tts miễn phí, giọng Việt tự nhiên, có cache theo text.

**Hệ quả:** Thoại là nguồn chân lý về thời lượng cảnh; ElevenLabs để backlog Phase 4; phụ thuộc dịch vụ Microsoft (rủi ro thấp, có thể swap service của manim-voiceover).

## D003 — Pipeline = các tầng rời giao tiếp bằng file artifact (2026-07-08)

**Quyết định:** 6 tầng độc lập, mỗi tầng đọc artifact tầng trước / ghi artifact của mình (`analysis.md` → `storyboard.json` → `script.json` → `scenes/*.py` → `final.mp4`) trong `projects/<slug>/`.

**Lý do:** Chạy lại được từng tầng khi lỗi (không tốn lại toàn pipeline); artifact người đọc được → dễ debug và sửa tay; các tầng nâng cấp độc lập.

**Hệ quả:** Phải giữ schema ổn định (định nghĩa trong ARCHITECTURE.md); mở: chọn Claude API thuần hay Claude Agent SDK cho runner — chốt đầu Phase 1.

## D004 — Hai vòng lặp chất lượng bắt buộc ở tầng codegen (2026-07-08)

**Quyết định:** (1) Vòng sửa lỗi render: stderr → agent sửa → retry ≤4 vòng, quá thì đơn giản hoá scene; (2) Vòng QA thị giác: vision model chấm frame trích xuất (chữ đè, tràn khung, safe-zone) → sửa layout → re-render cảnh đó.

**Lý do:** Hai mode lỗi phổ biến nhất của Manim sinh bằng LLM: code không chạy, và code chạy nhưng layout xấu. Thiếu vòng 2 thì video "đúng mà không đăng được".

**Hệ quả:** Tốn thêm token + thời gian render lặp → giảm bằng render `-ql` trong vòng lặp và cache theo cảnh.

## D005 — UI desktop tái dùng Aether Studio design system từ VideoDubbing (2026-07-08)

**Bối cảnh:** User yêu cầu tham khảo `D:\AgenticAI\VideoDubbing\apps\desktop\src\components\ui`.

**Quyết định:** Phase 3 dùng Tauri + React + Tailwind v4; port nguyên `styles.css` tokens và `components/ui/` (Button, Panel, Field..., StepNavigation, VideoPreview); theo pattern màn hình steplist/joblist/pill có sẵn.

**Lý do:** Đồng nhất trải nghiệm giữa các app trong hệ sinh thái AgenticAI của user; components đã chạy thực tế với tiếng Việt; không tốn công thiết kế lại.

**Hệ quả:** VidMak UI mang tông kem-cam của Aether Studio (khác tông video đen-vàng — chấp nhận, một cái là tool, một cái là sản phẩm đầu ra); cần Node 22+.

## D006 — Định dạng output mặc định: 9:16, 720×1280@30fps, 60–90s (2026-07-08)

**Lý do:** Khớp Ref_Video.mp4 và mục tiêu short-form (TikTok/Reels/Shorts). Tỉ lệ khác để backlog Phase 4.

**Hệ quả:** `theme.py` cấu hình frame 8.0×14.22 + safe-zone; storyboard mặc định 5–9 cảnh.

## D007 — Conda env (không phải venv) + workflow "diff trước, commit sau khi duyệt" (2026-07-08)

**Bối cảnh:** PLAN.md ban đầu ghi `python -m venv .venv`. Khi bắt đầu Phase 0, kiểm tra máy thấy các project khác trong `D:\AgenticAI\` (aether-diarization, keeptrack, omnivoice) đều dùng conda env, không dùng venv. Đồng thời user yêu cầu quy trình phát triển "chuyên nghiệp": review code, xem diff, duyệt trước khi merge.

**Quyết định:**
1. Dùng **conda env tên `vidmak`** (Python 3.11), cài Manim qua **conda-forge** thay vì pip trực tiếp.
2. Workflow git: tôi thực hiện thay đổi và **trình diff**, **không tự commit** — chờ user xác nhận "OK" rồi mới commit. (Đã hỏi 2 lựa chọn khác — commit-mỗi-bước-nhỏ và nhánh-riêng-theo-phase — user chọn phương án này.)

**Lý do:** (1) Nhất quán với hệ sinh thái sẵn có của user; conda-forge có wheel/binary sẵn cho `pycairo`/`pangocairocffi` trên Windows, tránh lỗi build mà pip hay gặp. (2) User muốn kiểm soát chặt từng thay đổi trước khi nó vào lịch sử git, không muốn agent tự ý commit.

**Hệ quả:** Mọi lệnh trong tài liệu (CLAUDE.md) dùng `conda activate vidmak` thay vì kích hoạt venv; `.gitignore` không cần ignore thư mục venv nội bộ repo. Ở cuối mỗi hạng mục việc, phải dừng lại trình bày diff/tóm tắt thay đổi và đợi phản hồi trước khi chạy `git commit` — không gộp nhiều hạng mục lớn vào một lần duyệt.

## D008 — Hai sự cố cài đặt Phase 0 và cách xử lý (2026-07-08)

**Sự cố 1 — `conda install -c conda-forge manim` vào env mặc định bị lỗi DLL:** `import av` rồi `import cairo` đều báo `DLL load failed ... The specified procedure could not be found`. Nguyên nhân gốc: `channel_priority: flexible` trong cấu hình conda của máy khiến gói `zlib` được solve từ channel `defaults` thay vì `conda-forge`, gây lệch ABI với các thư viện C khác (cairo, pango, ffmpeg) vốn được build trên conda-forge. **Xử lý:** xoá env, tạo lại bằng `conda create -n vidmak -c conda-forge --override-channels python=3.11 manim -y` để ép toàn bộ dependency về cùng một channel nhất quán. Sau đó `manim --version` chạy sạch.

**Sự cố 2 — `manim-voiceover[edgetts]` không có `EdgeTTSService`:** Bản đang cài (`manim-voiceover` 0.4.0) đã **gỡ bỏ** service tích hợp cho Edge TTS mà nhiều tài liệu/tutorial cũ tham chiếu (`manim_voiceover.services.edgetts`) — extras hợp lệ của bản này chỉ còn `azure, elevenlabs, gemini, gtts, openai, pyttsx3, recorder, transcribe, translate`. **Xử lý:** viết adapter riêng [pipeline/manim_lib/edge_tts_service.py](pipeline/manim_lib/edge_tts_service.py) — subclass `SpeechService` (theo đúng mẫu `GTTSService` có sẵn), gọi thẳng package `edge-tts` (cài riêng qua `pip install edge-tts`). Đã cân nhắc hạ cấp `manim-voiceover` về bản cũ có `EdgeTTSService` sẵn, nhưng chọn viết adapter để giữ bản mới nhất tương thích với Manim 0.20.1, tránh rủi ro xung đột API khác.

**Hệ quả:** `pipeline/manim_lib/edge_tts_service.py` là một phần bắt buộc của môi trường, không phải file tạm — mọi scene dùng voice phải import từ đây thay vì `manim_voiceover.services.edgetts`. Đã xác nhận hoạt động: scene hello-world render ra MP4 720×1280@30fps có audio AAC đồng bộ, chữ tiếng Việt có dấu hiển thị đúng qua Pango, MathTex hiển thị đúng, tông màu khớp Ref_Video.mp4.
