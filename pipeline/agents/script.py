"""Layer 3 -- Script.

Input:  projects/<slug>/storyboard.json (written by layer 2).
Output: projects/<slug>/script.json -- Vietnamese narration per scene plus a
        short on-screen caption, keyed by the same scene ids as the storyboard.

This layer writes the *words the viewer hears*. The prompt asks for narration in
3Blue1Brown voice -- one continuous train of thought that mirrors the visual
morphs, intuition before formulas, formulas spoken in words (never raw LaTeX) --
sized to each scene's duration_hint so the whole thing lands near the target.

`narration` is the source of truth for timing: at codegen manim-voiceover
stretches each animation to the real TTS duration (ARCHITECTURE.md). So we do
NOT trust the model to time itself -- est_speech_seconds is computed here in
Python from a calibrated speaking rate, purely as a planning estimate.
"""

from __future__ import annotations

import json
from pathlib import Path

from llm import complete
from workspace import project_dir

# Calibrated for vi-VN edge-tts neural voices reading educational narration at a
# calm, clear pace (~192 syllables/min). Vietnamese writes one syllable per
# whitespace token, so token count ~= syllable count. Re-tune once real TTS
# durations are measured against this estimate (Phase 2 lint).
SPEECH_SYLLABLES_PER_SECOND = 3.2

SYSTEM = (
    "Bạn là người viết lời bình (narration) tiếng Việt cho video giải thích "
    "ngắn dọc 9:16 theo phong cách 3Blue1Brown. Giọng của bạn ấm áp, dẫn dắt "
    "như một người thầy cùng người xem khám phá — trực giác trước, gọi tên công "
    "thức bằng lời chứ không đọc ký hiệu. Bạn viết cho tai nghe: câu ngắn, nhịp "
    "tự nhiên, dễ đọc bằng giọng máy TTS. Chỉ xuất JSON hợp lệ, không kèm giải "
    "thích, không bọc trong markdown."
)

PROMPT_TEMPLATE = """Chủ đề: "{topic}"
Tổng thời lượng mục tiêu: khoảng {duration_target} giây.

Dưới đây là storyboard: các cảnh theo thứ tự, kèm mô tả hình ảnh đang chuyển động và ghi chú hình học. Viết lời bình tiếng Việt cho TỪNG cảnh, bám sát cái đang diễn ra trên màn hình.

=== STORYBOARD ===
{scene_block}
=== HẾT STORYBOARD ===

NGUYÊN TẮC VIẾT LỜI BÌNH (phong cách 3Blue1Brown):
- Một mạch liền: câu mở của mỗi cảnh nối tiếp ý cảnh trước, để cả video nghe như một dòng suy nghĩ liên tục — giống hình ảnh biến hình liên tục chứ không cắt rời.
- Trực giác trước công thức. Khi cần nói công thức, DIỄN ĐẠT BẰNG LỜI (vd "pi nhân tích phân của bình phương f của x"), TUYỆT ĐỐI không đọc ký hiệu LaTeX thô (không "backslash int", không "\\pi").
- Dẫn dắt bằng "chúng ta / hãy nhìn / bạn để ý", đặt câu hỏi gợi mở khi hợp lý.
- Viết cho tai nghe: câu ngắn, mỗi câu một ý, tránh mệnh đề lồng nhau — đây là văn bản sẽ đọc bằng giọng TTS.
- Nói về Ý NGHĨA của cái đang diễn ra, KHÔNG mô tả thao tác kỹ thuật ("bây giờ animation quay 3D", "camera chuyển góc").
- Bám ngân sách âm tiết mỗi cảnh (±20%) để tổng thời lượng khớp mục tiêu; đừng nhồi chữ.

onscreen_text:
- Một cụm chữ RẤT ngắn (tối đa ~8 từ) hiện lên màn hình như phụ đề nhấn ý cốt lõi của cảnh.
- KHÔNG chép nguyên câu thoại. Để chuỗi rỗng "" nếu cảnh không cần chữ.

CHỈ xuất một object JSON hợp lệ theo schema sau. id phải đúng y hệt storyboard, ĐỦ và ĐÚNG THỨ TỰ các cảnh, không kèm bất kỳ chữ nào ngoài JSON:
{{
  "scenes": [
    {{ "id": "s01_title", "narration": "<lời bình tiếng Việt>", "onscreen_text": "<cụm ngắn hoặc chuỗi rỗng>" }}
  ]
}}"""


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


def _count_syllables(text: str) -> int:
    """Approximate spoken-syllable count = whitespace tokens with a letter/digit.

    Vietnamese orthography writes each syllable as its own whitespace-delimited
    token, so this closely tracks how many syllables the voice actually speaks.
    Pure-punctuation tokens (e.g. a stray '-') are ignored.
    """
    return sum(1 for tok in text.split() if any(ch.isalnum() for ch in tok))


def _estimate_seconds(narration: str) -> float:
    """Planning-only estimate of TTS duration for a narration string."""
    syllables = _count_syllables(narration)
    return round(max(syllables / SPEECH_SYLLABLES_PER_SECOND, 0.5), 1)


def _scene_block(scenes: list) -> str:
    """Render storyboard scenes into the prompt, with a per-scene syllable budget."""
    lines: list[str] = []
    for sc in scenes:
        sid = str(sc.get("id", "")).strip()
        dur = sc.get("duration_hint")
        head = f"[{sid}] ~{dur} giây"
        try:
            budget = round(float(dur) * SPEECH_SYLLABLES_PER_SECOND)
            head += f" (khoảng {budget} âm tiết thoại)"
        except (TypeError, ValueError):
            pass
        lines.append(head)
        visual = str(sc.get("visual", "")).strip()
        if visual:
            lines.append(f"  Hình ảnh: {visual}")
        notes = str(sc.get("geometry_notes", "")).strip()
        if notes:
            lines.append(f"  Ghi chú hình học: {notes}")
        lines.append("")
    return "\n".join(lines).strip()


def validate(data: object, expected_ids: list[str]) -> list[str]:
    """Return human-readable structural problems; empty list means valid.

    The hard guard is that scene ids match the storyboard exactly (same set,
    same order) so codegen can pair each narration with its scene. Narration
    quality is shaped by the prompt, not asserted here.
    """
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["script phải là một object JSON"]

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return ["'scenes' phải là mảng không rỗng"]

    got_ids = [
        str(sc.get("id", "")).strip() if isinstance(sc, dict) else ""
        for sc in scenes
    ]
    if got_ids != expected_ids:
        problems.append(
            "danh sách id cảnh không khớp storyboard:\n"
            f"      storyboard: {expected_ids}\n"
            f"      script:     {got_ids}"
        )

    for i, sc in enumerate(scenes):
        where = f"scenes[{i}]"
        if not isinstance(sc, dict):
            problems.append(f"{where} phải là object")
            continue
        if not str(sc.get("narration", "")).strip():
            problems.append(f"{where} thiếu 'narration'")
        onscreen = sc.get("onscreen_text", "")
        if not isinstance(onscreen, str):
            problems.append(f"{where} 'onscreen_text' phải là chuỗi")
    return problems


def _build_script(data: dict) -> dict:
    """Shape the validated model output into the script.json contract."""
    out_scenes = []
    for sc in data["scenes"]:
        narration = str(sc["narration"]).strip()
        out_scenes.append(
            {
                "id": str(sc["id"]).strip(),
                "narration": narration,
                "est_speech_seconds": _estimate_seconds(narration),
                "onscreen_text": str(sc.get("onscreen_text", "")).strip(),
            }
        )
    return {"scenes": out_scenes}


def run_script(topic: str) -> Path:
    """Generate script.json from storyboard.json for `topic`; return its path."""
    proj = project_dir(topic)
    storyboard_path = proj / "storyboard.json"
    if not storyboard_path.exists():
        raise FileNotFoundError(
            f"Chưa có {storyboard_path.name}; chạy tầng Storyboard trước."
        )

    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard.get("scenes") or []
    expected_ids = [str(sc.get("id", "")).strip() for sc in scenes]
    duration_target = storyboard.get("total_duration_target", 90)

    raw = complete(
        SYSTEM,
        PROMPT_TEMPLATE.format(
            topic=storyboard.get("topic", topic),
            duration_target=duration_target,
            scene_block=_scene_block(scenes),
        ),
    )
    data = _extract_json(raw)
    problems = validate(data, expected_ids)
    if problems:
        raise ValueError(
            "script.json không hợp lệ:\n" + "\n".join(f"  - {p}" for p in problems)
        )

    out = proj / "script.json"
    out.write_text(
        json.dumps(_build_script(data), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out
