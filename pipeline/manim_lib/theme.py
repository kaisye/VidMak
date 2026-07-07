"""Shared visual theme for every VidMak Manim scene.

Every scene imports from here instead of hardcoding colors, fonts, or frame
dimensions -- keeps agent-generated scenes visually consistent with each
other and with the reference style (Ref_Video.mp4). See DESIGN.md section B
for the source spec.
"""

from __future__ import annotations

from manim import config, ManimColor, Text, MathTex

# --- Frame / output ---------------------------------------------------------
# 9:16 short-form, matches Ref_Video.mp4 (720x1280 @ 30fps).
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280
FPS = 30
FRAME_HEIGHT = 14.222222  # frame_width is derived by Manim from the pixel aspect ratio (-> 8.0)

# Safe-zone: keep primary content within this vertical band so it isn't
# covered by the banner (top) or platform UI chrome (bottom) once posted.
SAFE_ZONE_TOP = FRAME_HEIGHT / 2 - 1.2
SAFE_ZONE_BOTTOM = -FRAME_HEIGHT / 2 + 1.0

# --- Colors ------------------------------------------------------------------
# Named after their role in the reference video, not their hue, so scene
# code reads as intent (e.g. GOLD_ACCENT) rather than a color guess.
BG = ManimColor("#000000")
GOLD_ACCENT = ManimColor("#FFD700")  # titles, highlighted rectangle, formula box
CURVE_CYAN = ManimColor("#58C4DD")  # f(x) curve, 3D surfaces, geometry labels
AXIS_RED = ManimColor("#FC6255")  # x-axis, emphasis lines
AXIS_GREEN = ManimColor("#83C167")  # y-axis
TEXT_WHITE = ManimColor("#FFFFFF")  # narration captions, plain labels

# --- Typography --------------------------------------------------------------
# Text() uses Pango and renders Vietnamese diacritics correctly; MathTex() is
# LaTeX and must never receive Vietnamese text (it breaks the diacritics).
VIETNAMESE_FONT = "Cambria"


def configure() -> None:
    """Apply the 9:16 short-form frame config. Call once, before building
    any Mobject, at the top of a scene file (after the imports)."""
    config.pixel_width = VIDEO_WIDTH
    config.pixel_height = VIDEO_HEIGHT
    config.frame_rate = FPS
    config.frame_height = FRAME_HEIGHT
    config.background_color = BG


def vn_text(content: str, **kwargs) -> Text:
    """Text() preconfigured for Vietnamese narration/labels."""
    kwargs.setdefault("font", VIETNAMESE_FONT)
    kwargs.setdefault("color", TEXT_WHITE)
    return Text(content, **kwargs)


def formula(tex: str, **kwargs) -> MathTex:
    """MathTex() preconfigured with the theme's default formula color."""
    kwargs.setdefault("color", TEXT_WHITE)
    return MathTex(tex, **kwargs)
