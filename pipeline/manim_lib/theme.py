"""Shared visual theme for every VidMak Manim scene.

Every scene imports from here instead of hardcoding colors, fonts, or frame
dimensions -- keeps agent-generated scenes visually consistent with each
other and with the reference style (Ref_Video.mp4). See DESIGN.md section B
for the source spec.
"""

from __future__ import annotations

import os

from manim import config, ManimColor, Text, MathTex

# --- Frame / output ---------------------------------------------------------
# 9:16 short-form, matches Ref_Video.mp4 (720x1280 @ 30fps).
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280
FPS = 30
FRAME_HEIGHT = 14.222222  # 9:16 units; FRAME_WIDTH = FRAME_HEIGHT * 720/1280
FRAME_WIDTH = 8.0  # MUST be set explicitly: Cairo derives it from the pixel aspect,
# but the OpenGL camera reads config.frame_width directly and otherwise keeps the
# landscape default (14.222), giving a square frame that throws off-screen every
# fixed-in-frame overlay in 3D scenes (title/caption/formula). See DECISIONS D011.

# Draft mode (env VIDMAK_DRAFT truthy) renders at reduced pixel density + fps so
# the codegen render/repair loop is fast; the final pass renders full-res. Same
# 9:16 aspect and same FRAME_HEIGHT, so composition, layout and safe-zone are
# pixel-for-pixel identical -- only the sampling resolution changes. Manim's -ql
# flag can't do this because configure() must fix the 9:16 pixel size itself.
DRAFT_WIDTH = 360
DRAFT_HEIGHT = 640
DRAFT_FPS = 15

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


def draft_enabled() -> bool:
    """True when VIDMAK_DRAFT asks for the fast low-res render (dev/repair loop)."""
    return os.getenv("VIDMAK_DRAFT", "").strip().lower() in {"1", "true", "yes", "on"}


def configure() -> None:
    """Apply the 9:16 short-form frame config. Call once, before building
    any Mobject, at the top of a scene file (after the imports).

    Honors VIDMAK_DRAFT: draft renders at DRAFT_WIDTH x DRAFT_HEIGHT @ DRAFT_FPS,
    otherwise full VIDEO_WIDTH x VIDEO_HEIGHT @ FPS. FRAME_HEIGHT is fixed either
    way so the visible layout is unchanged."""
    draft = draft_enabled()
    config.pixel_width = DRAFT_WIDTH if draft else VIDEO_WIDTH
    config.pixel_height = DRAFT_HEIGHT if draft else VIDEO_HEIGHT
    config.frame_rate = DRAFT_FPS if draft else FPS
    config.frame_height = FRAME_HEIGHT
    config.frame_width = FRAME_WIDTH
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
