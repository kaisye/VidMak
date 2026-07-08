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

## D009 — Orchestration: plain Python + `openai` SDK trỏ proxy local, không framework (2026-07-08)

**Bối cảnh:** D003 để mở câu hỏi "runner dùng Claude API thuần hay Claude Agent SDK". User hỏi có nên dùng framework (LangGraph/CrewAI) không, và cung cấp một endpoint LLM cục bộ **OpenAI-compatible** (`http://localhost:20128/v1`, model `cx/gpt-5.5` — một proxy kiểu LiteLLM route nhiều provider).

**Quyết định:** Pipeline là **plain Python** điều phối tuần tự, gọi model qua gói **`openai`** trỏ `base_url` về proxy local. **Không** dùng LangGraph, CrewAI, hay Claude Agent SDK.

**Lý do:** Pipeline là dây chuyền tuyến tính 6 bước, không rẽ nhánh/không đa-agent thương lượng → CrewAI sai hình dạng, LangGraph thừa. Chỗ "agentic" duy nhất (vòng tự sửa lỗi codegen) chỉ là `while` chặn 4 vòng — framework giấu mất đúng chỗ cần kiểm soát (cap vòng, fallback đơn giản hoá, cache theo cảnh). Plain Python giữ được deterministic + rerun từng tầng (giá trị cốt lõi ở D003/D004) và ít dependency (Windows đã dính lỗi DLL ở Phase 0). Endpoint OpenAI-compatible nên `openai` SDK là client tự nhiên; Claude Agent SDK khó trỏ về endpoint này.

**Hệ quả:** Cài `openai` (2.44.0) vào env `vidmak`. Config qua env var (`VIDMAK_LLM_BASE_URL/_MODEL/_API_KEY`, default sẵn trong `pipeline/llm.py` trỏ proxy local — proxy không kiểm key, dùng placeholder `sk-local`). Mọi tầng gọi model qua `pipeline/llm.py`, không import `openai` trực tiếp → đổi endpoint/model chỉ sửa một chỗ. Để cửa mở: mỗi tầng viết thành hàm thuần `(artifact vào) → (artifact ra)`, nếu sau này cần rẽ nhánh/song song thật thì bọc thành node LangGraph mà không viết lại. Lưu ý vận hành: proxy tự chèn system prompt lớn kiểu codex (~2500 token) trước messages của mình → mỗi tầng phải đặt system prompt riêng để đè "tính cách" đó. Backend `cx/*` cần auth codex còn hiệu lực của user (đã gặp 401 "token invalidated" khi hết phiên).

## D010 — Scene sinh ra dùng flat import; render.py bơm PYTHONPATH (2026-07-08)

**Bối cảnh:** Tầng 4b sinh `projects/<slug>/scenes/*.py` cần gọi `manim_lib` (theme/components/axes/solids) nằm ở `pipeline/manim_lib/`. Hai phương án: biến manim_lib thành package cài được, hoặc giữ flat import và bơm đường dẫn khi render.

**Quyết định:** Scene sinh ra viết `from theme import ...` (flat, y hệt `hello.py`/`smoke.py`); `render.py` chạy manim bằng **subprocess** và đặt `PYTHONPATH=pipeline/manim_lib` cho process con.

**Lý do:** Một convention import duy nhất cho cả file tay lẫn file sinh — prompt codegen đơn giản và ví dụ ít mẫu hơn; không cần cài package/`pip -e` (tránh đụng quy tắc "cài qua conda-forge"); subprocess cô lập crash của scene khỏi pipeline và cho bắt stderr sạch cho vòng tự sửa.

**Hệ quả:** Scene không chạy trực tiếp bằng `manim render` tay trừ khi tự set PYTHONPATH; mở file scene trong IDE sẽ báo unresolved import (chấp nhận — file sinh ra không phải nơi dev sửa tay). `codegen.py` chặn cứng import ngoài whitelist (manim, manim_voiceover, edge_tts_service, theme, components, axes, solids).

## D011 — Render CPU/Cairo, không dùng GPU/OpenGL; thêm chế độ draft qua env (2026-07-08)

**Bối cảnh:** Render full-res bằng Cairo rất chậm với cảnh 3D (cảnh nặng >20 phút, 10GB RAM). Đã thử `--renderer=opengl` (GPU): nhanh (~3 phút full-res) và có audio, **nhưng** camera fixed-frame của OpenGL khoá khung ~8×4.5 unit, bỏ qua `config.frame_height=14.222` → toàn bộ chữ overlay (`add_fixed_in_frame_mobjects`: tiêu đề, caption, khung công thức) văng ngoài màn hình ở khung dọc 9:16. Đã xác nhận bằng scene dò tọa độ; đây là giới hạn của manim 0.20.1, không phải config.

**Quyết định:** Ở lại **Cairo (CPU)**. Bù tốc độ bằng ba đòn: (1) prompt codegen ép cảnh nhẹ (≤16 khối 3D, `cylinder_stack n≤12`, cấm Transform giữa nhiều khối đặc và mặt cong — dùng FadeOut/FadeIn); (2) chế độ **draft** qua env `VIDMAK_DRAFT` trong `theme.configure()` (360×640@15, cùng `frame_height` nên layout y hệt) cho vòng lặp dev; (3) render song song (D012). Nhân tiện phát hiện + sửa bug: `configure()` phải set cả `config.frame_width=8.0` (Cairo tự suy từ tỉ lệ pixel nhưng OpenGL đọc trực tiếp, mặc định 14.222 → khung vuông).

**Lý do:** Chữ đúng và đủ là yêu cầu cứng của video toán; OpenGL phá vỡ nó không sửa được ở tầng config. Cảnh nhẹ + song song đưa full-res 9 cảnh về ~10 phút wall-clock — đạt mục tiêu tốc độ mà không hy sinh chất lượng.

**Hệ quả:** `-ql` của manim CLI vô dụng với ta (configure() đè pixel size) — draft đi qua `VIDMAK_DRAFT`. Số đo tham chiếu (cảnh s04 nhẹ): draft 4.5 phút, full-res 8 phút, RAM ~0.5GB. Nếu tương lai manim sửa fixed-frame OpenGL thì mở lại đánh giá (ghi mục mới trỏ về đây).

## D012 — Render các cảnh song song bằng ThreadPoolExecutor (2026-07-08)

**Bối cảnh:** Mỗi cảnh là một subprocess manim đơn luồng ~0.5GB RAM (sau khi cảnh đã nhẹ theo D011); máy dev 16 core. Render tuần tự 9 cảnh full-res ≈ 45–70 phút.

**Quyết định:** `render_project(topic, workers=N)` render các cảnh song song qua `ThreadPoolExecutor` (thread chỉ chờ subprocess — không cần multiprocessing); mỗi process con bị giới hạn 1 thread BLAS (`OMP/OPENBLAS/MKL/NUMEXPR_NUM_THREADS=1`) để N worker chia core sạch.

**Lý do:** Các cảnh độc lập hoàn toàn (D003 áp dụng cả trong tầng render); wall-clock ≈ cảnh chậm nhất (~8–12 phút) thay vì tổng.

**Hệ quả:** Log các cảnh xen kẽ nhau (chấp nhận ở CLI; UI Phase 3 hiển thị theo cảnh); vòng tự sửa của một cảnh chạy tuần tự bên trong worker của nó; TTS gọi đồng thời nhiều request edge-tts (chưa thấy rate-limit, theo dõi thêm).
