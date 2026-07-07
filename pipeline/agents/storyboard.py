"""Layer 2 -- Storyboard.

Input:  projects/<slug>/analysis.md (written by layer 1).
Output: projects/<slug>/storyboard.json -- an ordered shot list that layer 4
        (codegen) turns into Manim scenes.

This is the pedagogical heart of the pipeline: it decides *what moves on
screen*. The prompt encodes 3Blue1Brown grammar -- one idea per scene, objects
that transform into the next scene instead of hard cuts, intuition before
formula -- plus the 9:16 / safe-zone / Text-vs-MathTex constraints from
ARCHITECTURE.md so the shot list is buildable, not just pretty prose.

The output is strict JSON matching the `storyboard.json` contract in
ARCHITECTURE.md; validate() guards the structure before it reaches codegen.
"""

from __future__ import annotations

import json
from pathlib import Path

from llm import complete
from workspace import project_dir

DEFAULT_DURATION = 90  # seconds; D006 target for short-form 9:16

# Stable menu of helper names codegen (Phase 1) will implement in
# manim_lib/components.py and solids.py. The storyboard may reference these so
# codegen reuses them instead of re-deriving geometry; an empty list means
# "draw it directly". Names are advisory -- validate() does not reject unknown
# helpers, it only checks they are strings.
KNOWN_HELPERS = [
    "components.title_card",
    "components.end_card",
    "components.formula_box",
    "components.caption",
    "components.brace_label",
    "solids.lathe_from_curve",
    "solids.disk_from_rect",
    "solids.cylinder_stack",
    "axes.plane_2d",
    "axes.axes_3d",
]

SYSTEM = (
    "Bạn là đạo diễn hình ảnh (visual director) chuyển tài liệu toán/khoa học "
    "thành storyboard cho video ngắn dọc 9:16 theo phong cách 3Blue1Brown. Bạn "
    "tư duy bằng chuyển động: mỗi cảnh một ý, đối tượng biến hình liên tục thay "
    "vì cắt cảnh rời rạc, trực giác đi trước công thức. Chỉ xuất JSON hợp lệ, "
    "không kèm giải thích, không bọc trong markdown."
)

PROMPT_TEMPLATE = """Chủ đề: "{topic}"
Thời lượng mục tiêu: khoảng {duration} giây.

Dưới đây là tài liệu phân tích do tầng trước sinh ra. Dựng storyboard bám sát nó, đặc biệt mục "## Hình ảnh hoá được".

=== TÀI LIỆU PHÂN TÍCH ===
{analysis}
=== HẾT TÀI LIỆU ===

NGUYÊN TẮC DỰNG CẢNH (phong cách 3Blue1Brown):
- Mỗi cảnh chỉ MỘT ý. Xây trực giác trước; công thức chỉ xuất hiện sau khi người xem đã "thấy" được ý tưởng.
- Liên tục thị giác: ưu tiên biến hình đối tượng của cảnh trước thành cảnh sau (mô tả rõ "từ X biến thành Y"), hạn chế cắt cảnh rời rạc.
- Chuyển động phải mang nghĩa: cái gì di chuyển/biến đổi là để giải thích, không trang trí.
- Mở đầu bằng cảnh tiêu đề; kết bằng end-card ngắn mời gọi học tiếp.

RÀNG BUỘC KỸ THUẬT (bắt buộc):
- Chia 5-9 cảnh, mỗi cảnh 6-15 giây, tổng xấp xỉ {duration} giây.
- Khung dọc 9:16. Chừa safe-zone: ~1.2 đơn vị phía trên (banner) và ~1.0 đơn vị phía dưới (UI nền tảng che) — không đặt nội dung quan trọng ở hai vùng này.
- Chữ tiếng Việt mô tả trong trường "visual". Công thức toán để ở "geometry_notes" dưới dạng LaTeX — KHÔNG trộn tiếng Việt có dấu vào LaTeX.
- "helpers": chỉ dùng tên trong danh sách dưới đây, hoặc để [] nếu cảnh tự vẽ. Đây là gợi ý cho tầng codegen tái sử dụng, không bắt buộc mỗi cảnh phải có.

DANH SÁCH HELPER CHO PHÉP:
{helpers}

CHỈ xuất một object JSON hợp lệ theo đúng schema sau, không kèm bất kỳ chữ nào ngoài JSON:
{{
  "topic": "{topic}",
  "audience": "<đối tượng người xem, suy từ chủ đề, vd 'học sinh THPT'>",
  "total_duration_target": {duration},
  "banner": {{ "text": "", "enabled": false }},
  "scenes": [
    {{
      "id": "s01_title",
      "visual": "<mô tả tiếng Việt: cái gì trên màn hình và nó chuyển động thế nào>",
      "geometry_notes": "<gợi ý kỹ thuật Manim + công thức LaTeX nếu có>",
      "duration_hint": 8,
      "helpers": ["components.title_card"]
    }}
  ],
  "endcard": {{ "lines": ["<2-3 dòng CTA IN HOA ngắn>"] }}
}}

Quy ước id: sxx_ten_ngan, đánh số 2 chữ số theo thứ tự (s01_, s02_, ...), phần tên bằng chữ thường không dấu."""


def _extract_json(raw: str) -> object:
    """Parse the model output into JSON, tolerating markdown fences / stray prose.

    We ask for bare JSON, but proxies sometimes wrap it in ```json fences or add
    a sentence. Slicing from the first '{' to the last '}' recovers the object
    in the common cases; json.loads raises (ValueError) if it is still malformed.
    """
    text = raw.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model không trả về JSON (không tìm thấy '{...}').")
    return json.loads(text[start : end + 1])


def validate(data: object) -> list[str]:
    """Return human-readable structural problems; empty list means valid.

    Guards only what codegen depends on (shape, unique ids, positive durations).
    Pedagogical quality is shaped by the prompt, not asserted here.
    """
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["storyboard phải là một object JSON"]

    if not str(data.get("topic", "")).strip():
        problems.append("thiếu 'topic'")

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        problems.append("'scenes' phải là mảng không rỗng")
        return problems
    if not 3 <= len(scenes) <= 12:
        problems.append(f"số cảnh nên trong khoảng 3-12, hiện có {len(scenes)}")

    seen_ids: set[str] = set()
    for i, sc in enumerate(scenes):
        where = f"scenes[{i}]"
        if not isinstance(sc, dict):
            problems.append(f"{where} phải là object")
            continue
        sid = str(sc.get("id", "")).strip()
        if not sid:
            problems.append(f"{where} thiếu 'id'")
        elif sid in seen_ids:
            problems.append(f"{where} trùng id '{sid}'")
        else:
            seen_ids.add(sid)
        if not str(sc.get("visual", "")).strip():
            problems.append(f"{where} thiếu 'visual'")
        dur = sc.get("duration_hint")
        if isinstance(dur, bool) or not isinstance(dur, (int, float)) or dur <= 0:
            problems.append(f"{where} 'duration_hint' phải là số dương")
        helpers = sc.get("helpers", [])
        if helpers is not None and not (
            isinstance(helpers, list) and all(isinstance(h, str) for h in helpers)
        ):
            problems.append(f"{where} 'helpers' phải là mảng chuỗi")
    return problems


def run_storyboard(topic: str, *, duration: int = DEFAULT_DURATION) -> Path:
    """Generate storyboard.json from analysis.md for `topic`; return its path."""
    proj = project_dir(topic)
    analysis_path = proj / "analysis.md"
    if not analysis_path.exists():
        raise FileNotFoundError(
            f"Chưa có {analysis_path.name}; chạy tầng Analysis trước."
        )

    analysis = analysis_path.read_text(encoding="utf-8")
    raw = complete(
        SYSTEM,
        PROMPT_TEMPLATE.format(
            topic=topic,
            duration=duration,
            helpers="\n".join(f"- {h}" for h in KNOWN_HELPERS),
            analysis=analysis,
        ),
    )
    data = _extract_json(raw)
    problems = validate(data)
    if problems:
        raise ValueError(
            "storyboard.json không hợp lệ:\n" + "\n".join(f"  - {p}" for p in problems)
        )

    out = proj / "storyboard.json"
    out.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out
