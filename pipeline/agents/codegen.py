"""Layer 4b -- Codegen (scene generation + repair prompts).

Input:  projects/<slug>/storyboard.json + script.json (layers 2 and 3).
Output: projects/<slug>/scenes/<id>.py -- one manim-voiceover Scene per storyboard
        scene, calling the manim_lib helpers and speaking the layer-3 narration.

This module owns everything *language-model* about layer 4: the prompt that turns
one storyboard scene into a renderable .py file, the prompt that repairs a scene
from a render error, static validation, and a guaranteed-renderable fallback.
It does NOT run manim -- that is render.py, which drives the repair loop and calls
back into repair_scene() here (ARCHITECTURE.md: codegen agent + render self-repair).

Generated scenes use flat imports (`from theme import ...`) exactly like the
hand-written manim_lib scenes (smoke.py, hello.py); render.py puts manim_lib on
PYTHONPATH so they resolve from projects/<slug>/scenes/ (DECISIONS.md D010).
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from llm import complete
from workspace import project_dir

DEFAULT_VOICE = "vi-VN-HoaiMyNeural"

# Modules a generated scene is allowed to import from. Anything else is a bug
# (an invented dependency, an asset loader, ...) and fails static validation.
_ALLOWED_IMPORT_ROOTS = {
    "manim",
    "manim_voiceover",
    "edge_tts_service",
    "theme",
    "components",
    "axes",
    "solids",
}

# Concise, exact API the model composes from. Getting these signatures right is
# what keeps generated scenes rendering on the first pass -- keep it in sync with
# manim_lib/{components,solids,axes,theme}.py.
HELPER_API = """=== THƯ VIỆN manim_lib (chỉ dùng đúng các hàm/hằng dưới đây) ===

theme:
  configure()                       # gọi MỘT lần ở đầu file, ngay sau import
  vn_text(content, color=..., **kw) -> Text   # MỌI chữ tiếng Việt đi qua đây (Pango, đúng dấu)
  formula(tex, color=...) -> MathTex          # CHỈ cho công thức LaTeX, KHÔNG bỏ tiếng Việt vào
  Hằng màu: BG, GOLD_ACCENT, CURVE_CYAN, AXIS_RED, AXIS_GREEN, TEXT_WHITE
  Hằng khung: FRAME_HEIGHT, SAFE_ZONE_TOP, SAFE_ZONE_BOTTOM  (nội dung nằm giữa BOTTOM..TOP)

components (overlay 2D, trả Mobject CHƯA đặt vị trí, trừ caption đã tự đặt):
  title_card(title, subtitle=None) -> VGroup   # tiêu đề vàng + phụ đề trắng nhỏ; tự đặt: .to_edge(UP, buff=1.3)
  caption(text, max_width=7.0) -> Text         # phụ đề trắng ĐÃ neo ở vùng an toàn dưới; chỉ cần FadeIn
  formula_box(formula_mobject, buff=0.25) -> VGroup  # bọc một MathTex (từ formula(...)) trong khung vàng bo góc
  brace_label(mobject, text, direction=DOWN) -> VGroup  # ngoặc dọc theo mobject + nhãn nhỏ tiếng Việt
  end_card(lines) -> VGroup                    # thẻ CTA viền vàng; dùng cho cảnh kết; lines từ storyboard.endcard

axes (hệ trục theo theme):
  plane_2d(x_range=(0,5,1), y_range=(0,4,1), x_length=6.0, y_length=6.0) -> Axes  # Ox đỏ, Oy xanh lá
      vẽ đồ thị:  curve = ax.plot(lambda x: <f>, x_range=[a, b], color=CURVE_CYAN)
      lấy điểm:   ax.c2p(x, y)   # coords-to-point
  axes_3d(x_range=(-1,5,1), y_range=(-3,3,1), z_range=(-3,3,1), ...) -> ThreeDAxes  # map 1:1, khớp solids

solids (khối tròn xoay quanh trục Ox, dựng ở toạ độ thô 1:1 -> đặt cùng axes_3d):
  lathe_from_curve(func, x_range=(a,b), resolution=(24,32)) -> Surface  # quay y=func(x) quanh Ox
  disk_from_rect(radius, x_center=0.0, thickness=0.2) -> Cylinder       # một đĩa mỏng tại (x_center,0,0)
  cylinder_stack(func, x_range=(a,b), n=12) -> VGroup                   # chồng đĩa Riemann

edge_tts_service:
  EdgeTTSService(voice="vi-VN-HoaiMyNeural")   # truyền cho self.set_speech_service(...)
"""

# One worked scene the model mirrors for structure (imports, configure, single
# voiceover block, tracker-timed plays). Deliberately a *different* scene than any
# real one and free of triple quotes / backslashes so it embeds cleanly here.
EXAMPLE_2D = """# s00_vi_du — lát mỏng quay thành đĩa (ví dụ cấu trúc, không phải cảnh thật).

from manim import Create, FadeIn, UP, Write
from manim_voiceover import VoiceoverScene

from edge_tts_service import EdgeTTSService
from theme import CURVE_CYAN, configure, vn_text
from axes import plane_2d
from components import brace_label, caption, title_card

configure()

NARRATION = "..."


class S00ViDu(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="vi-VN-HoaiMyNeural"))

        title = title_card("Một lát cắt").to_edge(UP, buff=1.3)
        ax = plane_2d(x_range=(0, 5, 1), y_range=(0, 4, 1)).scale(0.7).move_to([0, 0.4, 0])
        curve = ax.plot(lambda x: 0.5 * x + 0.6, x_range=[0, 4], color=CURVE_CYAN)
        bl = brace_label(curve, "chiều cao f(x)", direction=UP)
        cap = caption("Chiều cao thành bán kính")

        with self.voiceover(text=NARRATION) as tracker:
            self.play(Write(title), run_time=tracker.duration * 0.25)
            self.play(Create(ax), Create(curve), run_time=tracker.duration * 0.40)
            self.play(FadeIn(bl), FadeIn(cap), run_time=tracker.duration * 0.35)
        self.wait(0.3)
"""

RULES = """=== QUY TẮC BẮT BUỘC ===
1. Xuất DUY NHẤT nội dung một file Python hoàn chỉnh. KHÔNG markdown, KHÔNG giải thích, KHÔNG ```.
2. Đúng MỘT class Scene, tên chính xác là {class_name}.
   - Cảnh 2D:  class {class_name}(VoiceoverScene)
   - Cảnh 3D (có khối tròn xoay/axes_3d/xoay camera):  class {class_name}(VoiceoverScene, ThreeDScene)
     và dòng đầu construct sau set_speech_service:  self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES)
3. Gọi configure() một lần ở cấp module, ngay sau các import.
4. Dòng đầu tiên trong construct():  self.set_speech_service(EdgeTTSService(voice="vi-VN-HoaiMyNeural"))
5. Bọc TOÀN BỘ hoạt ảnh trong ĐÚNG MỘT khối:  with self.voiceover(text=NARRATION) as tracker:
   Chia thời lượng qua run_time=tracker.duration * w (các w cộng lại xấp xỉ 1). Có thể self.wait(...) ngắn ở cuối.
   Module PHẢI có đúng một dòng:  NARRATION = "..."   (nội dung sẽ được ghi đè tự động — cứ để chuỗi bất kỳ).
6. Tiếng Việt LUÔN qua vn_text()/các helper; công thức LUÔN qua formula()/MathTex(); TUYỆT ĐỐI không trộn tiếng Việt có dấu vào MathTex.
7. Màu CHỈ lấy từ hằng trong theme (GOLD_ACCENT, CURVE_CYAN, ...). Cấm mã hex, cấm tên màu lạ.
8. Nội dung nằm trong vùng an toàn (y trong khoảng SAFE_ZONE_BOTTOM..SAFE_ZONE_TOP). Tiêu đề đặt gần đỉnh (.to_edge(UP, buff=1.3)); phụ đề dùng caption() (đã tự neo).
8b. CHỈ đặt MỘT cụm chữ ở vùng đáy: HOẶC caption() HOẶC một vn_text neo đáy — KHÔNG dùng cả hai (chúng sẽ đè lên nhau). Đừng chồng hai text ở cùng vị trí; mỗi text một chỗ riêng, cách nhau rõ.
9. Trong cảnh 3D, MỌI overlay phẳng (title_card, caption, formula_box, chữ vn_text) phải gọi self.add_fixed_in_frame_mobjects(m) trước khi animate để nó luôn quay mặt về người xem.
10. Chỉ import từ: manim, manim_voiceover, edge_tts_service, theme, components, axes, solids. Ngoài helper đã liệt kê, được dùng mobject Manim cơ bản (Dot, Line, Arrow, SurroundingRectangle, VGroup, ...) nhưng vẫn lấy màu từ theme.
11. Không đọc/ghi file, không mạng, không ảnh/SVG/font ngoài.

=== HIỆU NĂNG (render bằng Cairo rất chậm với 3D — bắt buộc giữ cảnh NHẸ) ===
12. Tổng số mobject 3D nặng (đĩa/khối/mặt) trong một cảnh KHÔNG quá 16. Với cylinder_stack, n ≤ 12. KHÔNG tạo hàng chục đĩa.
13. Đừng dùng nhiều Surface/lathe_from_curve cùng lúc; tối đa 1–2. Giữ resolution mặc định của helper, KHÔNG tăng lên.
14. TUYỆT ĐỐI không Transform/ReplacementTransform giữa NHIỀU khối đặc (ví dụ chồng chục đĩa) và một mặt cong — cực kỳ chậm. Muốn chuyển từ chồng đĩa sang khối mịn: FadeOut(chồng đĩa) rồi FadeIn(mặt lathe).
15. Ưu tiên ít mobject, hoạt ảnh đơn giản (FadeIn/FadeOut/Create/Write). Tránh Rotate/animate.set_opacity trên nhóm đông mobject 3D.
16. CẤM đặt opacity = 0 rồi FadeIn (FadeIn lấy opacity hiện tại làm đích → fade 0→0, mobject không bao giờ hiện). Muốn một mobject xuất hiện muộn: add_fixed_in_frame_mobjects(m) nếu là overlay 3D rồi self.remove(m), sau đó self.play(FadeIn(m)); hoặc đơn giản là chỉ FadeIn(m) mà không thêm m vào scene trước đó.
17. TUYỆT ĐỐI KHÔNG vô hiệu hoá lời bình để né lỗi: cấm ghi đè self.voiceover, cấm tự định nghĩa lớp/hàm voiceover hay tracker "giả/câm" (Silent...), cấm bỏ set_speech_service. Thoại là bắt buộc — luôn dùng self.voiceover(text=NARRATION) thật của VoiceoverScene với self.set_speech_service(EdgeTTSService(...)). Nếu voiceover gây lỗi, sửa NGUYÊN NHÂN thật, đừng thay bằng bản câm.
"""

SYSTEM_GENERATE = (
    "Bạn là kỹ sư viết mã Manim (manim-voiceover) cho video giải thích dọc 9:16 "
    "phong cách 3Blue1Brown. Bạn sinh ra MỘT file Python một cảnh, render sạch bằng "
    "manim, dùng đúng thư viện manim_lib được cấp và tuân thủ tuyệt đối các quy tắc. "
    "Chỉ xuất mã Python thô, không kèm chữ nào khác."
)

SYSTEM_REPAIR = (
    "Bạn là kỹ sư sửa lỗi Manim. Người ta đưa cho bạn một file cảnh Manim và thông "
    "báo lỗi khi render. Hãy sửa để nó render sạch, thay đổi ÍT nhất có thể, giữ "
    "nguyên tên class, cấu trúc voiceover và tinh thần hình ảnh. Vẫn tuân thủ mọi "
    "quy tắc. Chỉ xuất lại toàn bộ file Python đã sửa, không kèm chữ nào khác."
)


def class_name_for(scene_id: str) -> str:
    """Deterministic PascalCase class name from a scene id ('s01_title' -> 'S01Title').

    render.py derives the same name to invoke the scene, so codegen and render
    never disagree on what to call manim with.
    """
    parts = [p for p in scene_id.split("_") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) or "Scene"


def _is_3d(spec: dict) -> bool:
    """Heuristic: does this scene need a 3D camera (solids / 3D axes / camera moves)?"""
    helpers = spec.get("helpers") or []
    if any(str(h).startswith("solids.") for h in helpers) or "axes.axes_3d" in helpers:
        return True
    notes = str(spec.get("geometry_notes", ""))
    return bool(re.search(r"3d|threed|camera|phi\s*=|theta\s*=", notes, re.IGNORECASE))


def _extract_code(raw: str) -> str:
    """Recover the Python source from the model output, tolerating ``` fences."""
    text = raw.strip()
    fence = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if fence:
        return fence.group(1).strip() + "\n"
    return text + ("\n" if not text.endswith("\n") else "")


def inject_narration(code: str, narration: str) -> str:
    """Force the module's NARRATION to the exact script narration.

    The voice reads whatever NARRATION holds, so we never trust the model to copy
    the narration verbatim -- we overwrite the single-line assignment (or insert
    one after configure()) with the canonical string from script.json.
    """
    canonical = "NARRATION = " + json.dumps(narration, ensure_ascii=False)
    if re.search(r"(?m)^NARRATION\s*=.*$", code):
        return re.sub(r"(?m)^NARRATION\s*=.*$", lambda _m: canonical, code, count=1)
    if re.search(r"(?m)^configure\(\)\s*$", code):
        return re.sub(
            r"(?m)^configure\(\)\s*$",
            lambda _m: "configure()\n\n" + canonical,
            code,
            count=1,
        )
    return canonical + "\n\n" + code


def validate_scene_code(code: str, class_name: str) -> list[str]:
    """Static checks before we spend a render on the file; empty list means OK.

    Catches the cheap-to-detect mistakes (won't parse, wrong/missing class, no
    voiceover, forbidden import) so the render loop only pays for real runtime
    errors. Visual correctness is not asserted here -- that is the QA pass (4b V2).
    """
    problems: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"lỗi cú pháp Python: {exc.msg} (dòng {exc.lineno})"]

    if not re.search(rf"(?m)^class\s+{re.escape(class_name)}\b", code):
        problems.append(f"thiếu class tên đúng '{class_name}'")
    if "set_speech_service" not in code:
        problems.append("thiếu self.set_speech_service(EdgeTTSService(...))")
    if "self.voiceover(" not in code:
        problems.append("thiếu khối with self.voiceover(text=NARRATION)")
    if not re.search(r"(?m)^configure\(\)\s*$", code):
        problems.append("thiếu lời gọi configure() ở cấp module")
    # Guard against the repair loop "cheating" a render error by stubbing out the
    # voiceover (a silent tracker / reassigned self.voiceover) -- that renders fine
    # but ships a scene with no narration audio.
    if re.search(r"self\.voiceover\s*=", code) or re.search(r"(?m)^\s*def\s+voiceover\b", code):
        problems.append("không được ghi đè self.voiceover (phải dùng voiceover thật của VoiceoverScene)")
    if re.search(r"[Ss]ilent(Voiceover|Tracker|Context)", code):
        problems.append("không được dùng tracker/voiceover câm giả (Silent...) — thoại là bắt buộc")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in _ALLOWED_IMPORT_ROOTS:
                    problems.append(f"import không cho phép: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root and root not in _ALLOWED_IMPORT_ROOTS:
                problems.append(f"import không cho phép: from {node.module}")
    return problems


def _generate_prompt(spec: dict) -> str:
    """Assemble the per-scene generation prompt from the storyboard/script spec."""
    kind = "3D (VoiceoverScene, ThreeDScene)" if _is_3d(spec) else "2D (VoiceoverScene)"
    prev = spec.get("prev_visual")
    prev_line = (
        f"\nBối cảnh: cảnh ngay trước kết ở hình ảnh: {prev}\n"
        "Mở cảnh này nối tiếp trạng thái đó (liên tục thị giác)."
        if prev
        else ""
    )
    header = (
        f"Sinh file cảnh Manim cho cảnh id = {spec['id']}.\n"
        f"Tên class BẮT BUỘC: {spec['class']}\n"
        f"Loại cảnh gợi ý: {kind}\n"
        f"Thời lượng ước lượng: ~{spec.get('duration_hint')} giây.\n"
        f"Helper storyboard gợi ý (ưu tiên dùng, nhưng tự quyết cho hợp lý): "
        f"{spec.get('helpers')}\n"
        f"{prev_line}\n"
        f"HÌNH ẢNH (visual): {spec.get('visual', '')}\n"
        f"GHI CHÚ HÌNH HỌC (geometry_notes): {spec.get('geometry_notes', '')}\n"
        f"CHỮ TRÊN MÀN HÌNH (onscreen_text): {json.dumps(spec.get('onscreen_text', ''), ensure_ascii=False)}\n"
        f"LỜI BÌNH (narration, để tham chiếu nhịp — sẽ tự đưa vào NARRATION):\n"
        f"{json.dumps(spec.get('narration', ''), ensure_ascii=False)}\n"
    )
    return (
        header
        + "\n"
        + HELPER_API
        + "\n=== VÍ DỤ CẤU TRÚC ===\n"
        + EXAMPLE_2D
        + "=== HẾT VÍ DỤ ===\n\n"
        + RULES.format(class_name=spec["class"])
    )


def generate_scene(spec: dict) -> str:
    """Generate one renderable scene file (code cleaned + narration pinned)."""
    raw = complete(SYSTEM_GENERATE, _generate_prompt(spec))
    return inject_narration(_extract_code(raw), spec["narration"])


def repair_scene(code: str, error: str, spec: dict) -> str:
    """Ask the model to fix `code` given a render/static `error`; return pinned code."""
    user = (
        f"Cảnh id = {spec['id']}, class BẮT BUỘC giữ nguyên: {spec['class']}.\n\n"
        "=== FILE HIỆN TẠI ===\n"
        f"{code}\n"
        "=== HẾT FILE ===\n\n"
        "=== LỖI KHI RENDER (hoặc lỗi kiểm tra tĩnh) ===\n"
        f"{error}\n"
        "=== HẾT LỖI ===\n\n"
        + HELPER_API
        + "\n"
        + RULES.format(class_name=spec["class"])
        + "\nSửa file để render sạch, đổi ít nhất có thể. Xuất lại TOÀN BỘ file."
    )
    raw = complete(SYSTEM_REPAIR, user)
    return inject_narration(_extract_code(raw), spec["narration"])


def fallback_scene_code(spec: dict) -> str:
    """A minimal scene guaranteed to render (title + narration), used after 4 failed
    repair rounds so the pipeline still produces a clip for this beat."""
    onscreen = (spec.get("onscreen_text") or "").strip() or spec["id"]
    return (
        f"# {spec['id']} — bản tối giản (fallback sau khi codegen thất bại).\n\n"
        "from manim import FadeIn, FadeOut\n"
        "from manim_voiceover import VoiceoverScene\n\n"
        "from edge_tts_service import EdgeTTSService\n"
        "from theme import GOLD_ACCENT, configure, vn_text\n\n"
        "configure()\n\n"
        f"NARRATION = {json.dumps(spec['narration'], ensure_ascii=False)}\n"
        f"ONSCREEN = {json.dumps(onscreen, ensure_ascii=False)}\n\n\n"
        f"class {spec['class']}(VoiceoverScene):\n"
        "    def construct(self):\n"
        '        self.set_speech_service(EdgeTTSService(voice="vi-VN-HoaiMyNeural"))\n'
        "        label = vn_text(ONSCREEN, color=GOLD_ACCENT).scale(0.7)\n"
        "        if label.width > 7.0:\n"
        "            label.scale_to_fit_width(7.0)\n"
        "        with self.voiceover(text=NARRATION) as tracker:\n"
        "            self.play(FadeIn(label), run_time=min(1.0, tracker.duration * 0.3))\n"
        "            self.wait(max(tracker.duration - 1.3, 0.2))\n"
        "            self.play(FadeOut(label), run_time=0.5)\n"
    )


def scene_specs(topic: str) -> list[dict]:
    """Pair storyboard scenes with their script narration into codegen specs.

    Shared by run_codegen (to generate) and render.py (to render), so both walk
    the same scenes, files and class names. Order follows the storyboard.
    """
    proj = project_dir(topic)
    storyboard_path = proj / "storyboard.json"
    script_path = proj / "script.json"
    if not storyboard_path.exists():
        raise FileNotFoundError(f"Chưa có {storyboard_path.name}; chạy tầng Storyboard trước.")
    if not script_path.exists():
        raise FileNotFoundError(f"Chưa có {script_path.name}; chạy tầng Script trước.")

    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    script = json.loads(script_path.read_text(encoding="utf-8"))
    script_by_id = {str(sc.get("id", "")).strip(): sc for sc in script.get("scenes", [])}
    scenes_dir = proj / "scenes"

    specs: list[dict] = []
    prev_visual: str | None = None
    for sc in storyboard.get("scenes", []):
        sid = str(sc.get("id", "")).strip()
        ssc = script_by_id.get(sid, {})
        specs.append(
            {
                "id": sid,
                "class": class_name_for(sid),
                "file": scenes_dir / f"{sid}.py",
                "narration": str(ssc.get("narration", "")).strip(),
                "onscreen_text": str(ssc.get("onscreen_text", "")).strip(),
                "visual": str(sc.get("visual", "")).strip(),
                "geometry_notes": str(sc.get("geometry_notes", "")).strip(),
                "duration_hint": sc.get("duration_hint"),
                "helpers": sc.get("helpers") or [],
                "prev_visual": prev_visual,
            }
        )
        prev_visual = str(sc.get("visual", "")).strip() or prev_visual
    return specs


def write_scene(spec: dict) -> Path:
    """Generate, statically validate (one corrective pass), and write one scene file."""
    code = generate_scene(spec)
    problems = validate_scene_code(code, spec["class"])
    if problems:
        code = repair_scene(code, "Lỗi kiểm tra tĩnh:\n- " + "\n- ".join(problems), spec)
    spec["file"].parent.mkdir(parents=True, exist_ok=True)
    spec["file"].write_text(code, encoding="utf-8")
    return spec["file"]


def run_codegen(topic: str) -> list[dict]:
    """Generate projects/<slug>/scenes/*.py for every storyboard scene.

    Only writes the scene sources -- render.py (self-repair) turns them into clips.
    Returns the scene specs (id/class/file/...) for the render step to consume.
    """
    specs = scene_specs(topic)
    for spec in specs:
        print(f"  gen  {spec['id']}  ->  scenes/{spec['id']}.py")
        write_scene(spec)
    return specs
