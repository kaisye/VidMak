# DESIGN — Hệ thống thiết kế VidMak

Hai phần tách biệt: **(A)** UI của app desktop — tái dùng design system "Aether Studio" từ dự án VideoDubbing; **(B)** style guide cho video Manim — theo video tham chiếu Ref_Video.mp4.

---

## A. App UI — Aether Studio tokens

**Nguồn:** `D:\AgenticAI\VideoDubbing\apps\desktop\src\styles.css` và `src\components\ui\`. Khi scaffold Phase 3, port nguyên hai file/thư mục này, không viết lại.

**Stack:** Tauri + React + TypeScript + Tailwind v4 (`@import "tailwindcss"`) + `clsx` + `lucide-react`. Style qua **CSS variables**, không hardcode màu trong component.

### Tokens chính

```css
/* Nền & bề mặt — tông kem ấm, light mode */
--canvas: #f5efe4;        --canvas-deep: #eee4d5;
--surface: #fffdf8;       --surface-muted: #f9f5ed;   --surface-raised: #ffffff;

/* Chữ */
--text-primary: #1d1b18;  --text-secondary: #716b63;  --text-tertiary: #928a80;

/* Viền */
--border: rgba(63,53,43,.18);  --border-strong: rgba(63,53,43,.3);

/* Màu chủ đạo — cam đất */
--primary: #e67831;  --primary-hover: #c85d1f;  --primary-soft: #f9dfc5;

/* Ngữ nghĩa */
--success: #47785c;  --info: #5f5884;  --warning: #81651f;  --danger: #b6342d;
/* mỗi màu có biến *-soft cho nền nhạt */

/* Bo góc & bóng */
--radius-button: 10px;  --radius-panel: 16px;  --radius-pill: 999px;
--shadow-panel: 0 18px 45px rgba(73,53,31,.1);
--shadow-focus: 0 0 0 3px rgba(230,120,49,.18);
```

Nền body có radial-gradient vàng nhạt hai góc trên. Font hệ thống (`-apple-system, "Segoe UI", ...`) — **không dùng font display fancy vì phải hiển thị tiếng Việt**. Mono: `ui-monospace, "Cascadia Code", Consolas`.

### Component inventory (port từ VideoDubbing)

| File | Components | Ghi chú |
|---|---|---|
| `button.tsx` | `Button` (primary/secondary/ghost/danger; sm/md/lg; loading, leadingIcon), `IconButton` | secondary là mặc định |
| `card.tsx` | `Panel` (elevated?) | section bo `--radius-panel` |
| `form.tsx` | `Field`, `TextField`, `TextArea`, `Select`, `SegmentedControl`, `Switch`, `Slider` | Field = label + hint wrapper |
| `feedback.tsx` | `InlineNotice` (info/success/warning/danger), `LoadingState` | icon lucide theo tone |
| `navigation.tsx` | `StepNavigation` | dùng cho wizard nhiều bước |
| `media.tsx` | `VideoPreview` | dùng cho màn Result |

### Pattern màn hình (từ legacy chrome VideoDubbing, tái dụng cho VidMak)

- **Topbar**: brand + nav tabs (`.nav button.active` → nền `--primary-soft`, chữ `--primary-hover`)
- **Progress**: `.steplist` (li.done / li.active) — khớp 6 tầng pipeline; `.progress-track/.progress-fill`; `.logbox` nền tối `#1c1a17` cho log render
- **History**: `.joblist` + `.jobrow` + `.pill` (ready/failed/run/idle)
- **Thông báo**: `.banner` err/ok/warn/info

---

## B. Video style guide — Manim (theo Ref_Video.mp4)

Mã hoá thành `pipeline/manim_lib/theme.py`, agent codegen bắt buộc import, không tự chế màu.

### Khung hình

- 720×1280 @ 30fps (9:16); Manim config: `pixel_width=720, pixel_height=1280, frame_width=8.0, frame_height=14.22`
- **Safe-zone**: chừa 1.2 unit trên cho banner, 1.0 unit dưới (bị UI platform che)

### Bảng màu (khớp frame đã phân tích từ Ref_Video)

| Vai trò | Màu | Dùng cho |
|---|---|---|
| Nền | `#000000` (đen tuyền) | mọi scene |
| Tiêu đề / nhấn mạnh | vàng gold `#FFD700` (Manim `YELLOW` ~ `#FFFF00` cho highlight) | tiêu đề, khung công thức, hình chữ nhật Riemann highlight |
| Đường cong / đồ thị | cyan `#58C4DD` (Manim `BLUE`) | f(x), mặt 3D, chú thích hình học |
| Trục hoành / cảnh báo | đỏ cam `#FC6255` (Manim `RED`) | trục Ox, câu nhấn cảm xúc |
| Trục tung | xanh lá `#83C167` (Manim `GREEN`) | trục Oy |
| Chữ thường | trắng `#FFFFFF` | thoại on-screen, chú thích |
| Mặt 3D | cyan checkerboard (mặc định `Surface` Manim, opacity ~0.7) + viền `#FFD700` | lát trụ, khối tròn xoay |

### Typography & thành phần lặp lại

- Công thức: `MathTex` (Computer Modern mặc định) — reveal bằng `Write()`
- Lời văn tiếng Việt: `Text()` font serif ("Cambria"/"Times New Roman" cho khớp cảm giác LaTeX của video mẫu — chốt khi làm Phase 0)
- **Banner** (components.banner): 2 dòng chữ vàng, cỡ nhỏ, ghim mép trên mọi scene
- **Khung công thức** (components.formula_box): `SurroundingRectangle` viền vàng bo góc quanh công thức chốt
- **Brace chú thích** (components.labeled_brace): `Brace` + label kiểu "Bề rộng = dx"
- **End-card** (components.end_card): `RoundedRectangle` viền vàng, 3 dòng text căn giữa (tiêu đề trắng / nhấn đỏ cam / phụ vàng)

### Nhịp animation

- Vẽ trục/đường: `Create()` 1–2s; công thức: `Write()`; chuyển 2D→3D: `move_camera` mượt ~2s
- Mỗi cảnh mở bằng câu thoại, animation chính chạy trong `tracker.duration` — không có khoảng chết > 1.5s không animation
- Kết mỗi ý bằng 0.5–1s giữ hình (`self.wait`) trước khi chuyển cảnh
