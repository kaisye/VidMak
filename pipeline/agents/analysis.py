"""Layer 1 -- Analysis.

Input:  a raw topic string.
Output: projects/<slug>/analysis.md -- a pedagogical breakdown that layer 2
        (storyboard) reads to plan the visuals.

The prompt asks for an *intuition-first* decomposition (definition, the key
geometric intuition, core formulas, visualizable scenes, misconceptions)
because the whole point downstream is to turn this into a 3Blue1Brown-style
visual explanation, not a wall of formulas. Vietnamese narration text uses
Text()/Pango later, so we keep the analysis in Vietnamese from the start.
"""

from __future__ import annotations

from pathlib import Path

from llm import complete
from workspace import project_dir

SYSTEM = (
    "Bạn là chuyên gia sư phạm toán và khoa học, chuẩn bị tư liệu nền để dựng "
    "một video ngắn 60-90 giây theo phong cách 3Blue1Brown (giải thích trực "
    "quan bằng hình học). Chỉ xuất Markdown tiếng Việt, đi thẳng vào nội dung, "
    "không rào đón, không hỏi lại."
)

PROMPT_TEMPLATE = """Chủ đề: "{topic}"
Đối tượng: người học muốn hiểu trực giác, không chỉ thuộc công thức.

Viết tài liệu phân tích bằng Markdown, giữ nguyên các heading dưới đây theo đúng thứ tự:

## Định nghĩa cốt lõi
Phát biểu chính xác nhưng ngắn gọn.

## Trực giác
Ý tưởng hình học/trực quan then chốt — điều gì khiến khái niệm này "bấm sáng" trong đầu người học.

## Công thức chính
Các công thức quan trọng viết bằng LaTeX inline ($...$), kèm giải thích ý nghĩa từng ký hiệu.

## Hình ảnh hoá được
Liệt kê 3-6 cảnh hình học có thể dựng bằng Manim để giải thích. Mỗi bullet mô tả rõ cái gì chuyển động hoặc biến đổi trên màn hình.

## Hiểu lầm thường gặp
1-3 lỗi tư duy phổ biến mà video nên đính chính.

## Ứng dụng / ví dụ đời thực
1-2 ví dụ ngắn tạo động lực."""


def run_analysis(topic: str) -> Path:
    """Generate analysis.md for `topic` and return its path."""
    content = complete(SYSTEM, PROMPT_TEMPLATE.format(topic=topic))
    out = project_dir(topic) / "analysis.md"
    out.write_text(content.strip() + "\n", encoding="utf-8")
    return out
