"""Reusable 2D overlay components for VidMak scenes.

These are the recurring text/annotation pieces the storyboard references by name
(components.title_card, components.caption, ...). Codegen (layer 4) calls these
instead of re-deriving layout, so every generated scene stays visually
consistent with the reference style. All colors/fonts come from theme.py --
nothing here hardcodes a hue. See DESIGN.md section B.

Helpers return un-positioned Mobjects (the caller places them) except caption(),
which is defined by its home in the bottom safe zone.
"""

from __future__ import annotations

from manim import (
    DOWN,
    UP,
    Brace,
    Mobject,
    RoundedRectangle,
    SurroundingRectangle,
    Text,
    VGroup,
)

from theme import (
    AXIS_RED,
    GOLD_ACCENT,
    SAFE_ZONE_BOTTOM,
    TEXT_WHITE,
    vn_text,
)

# End-card lines cycle through: white heading, red-orange emphasis, gold tail
# (DESIGN.md B: "tiêu đề trắng / nhấn đỏ cam / phụ vàng").
_ENDCARD_COLORS = [TEXT_WHITE, AXIS_RED, GOLD_ACCENT]


def title_card(title: str, subtitle: str | None = None) -> VGroup:
    """Gold title with an optional small white subtitle stacked below it."""
    group = VGroup()
    heading = vn_text(title, color=GOLD_ACCENT).scale(1.1)
    group.add(heading)
    if subtitle:
        sub = vn_text(subtitle, color=TEXT_WHITE).scale(0.5)
        sub.next_to(heading, DOWN, buff=0.35)
        group.add(sub)
    return group


def caption(text: str, max_width: float = 7.0) -> Text:
    """White Vietnamese caption, shrunk to fit and parked in the bottom safe zone."""
    txt = vn_text(text, color=TEXT_WHITE).scale(0.55)
    if txt.width > max_width:
        txt.scale_to_fit_width(max_width)
    txt.move_to([0, SAFE_ZONE_BOTTOM + 0.4, 0])
    return txt


def formula_box(formula_mobject: Mobject, buff: float = 0.25) -> VGroup:
    """Wrap a settled formula in the gold rounded 'chốt' box."""
    box = SurroundingRectangle(
        formula_mobject, color=GOLD_ACCENT, corner_radius=0.15, buff=buff
    )
    return VGroup(formula_mobject, box)


def brace_label(mobject: Mobject, text: str, direction=DOWN) -> VGroup:
    """Brace along `mobject` on `direction`, with a small Vietnamese label."""
    brace = Brace(mobject, direction=direction, color=GOLD_ACCENT)
    label = vn_text(text, color=TEXT_WHITE).scale(0.5)
    label.next_to(brace, direction, buff=0.15)
    return VGroup(brace, label)


def end_card(lines: list[str]) -> VGroup:
    """Rounded gold-bordered card with centered CTA lines (2-3 recommended)."""
    texts = VGroup()
    for i, line in enumerate(lines):
        color = _ENDCARD_COLORS[i % len(_ENDCARD_COLORS)]
        texts.add(vn_text(line, color=color).scale(0.6))
    texts.arrange(DOWN, buff=0.4)
    box = RoundedRectangle(
        corner_radius=0.2,
        width=max(texts.width + 1.0, 4.0),
        height=texts.height + 1.0,
        color=GOLD_ACCENT,
    )
    box.move_to(texts)
    return VGroup(box, texts)
