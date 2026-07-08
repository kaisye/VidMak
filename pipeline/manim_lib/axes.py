"""Theme-aware coordinate systems (2D plane, 3D axes).

Thin wrappers over Manim's Axes / ThreeDAxes that apply the reference palette
(x-axis red, y-axis green -- DESIGN.md B) so codegen doesn't restate axis styling
in every scene. axes_3d defaults to a 1:1 data-to-scene mapping so raw-coordinate
solids from solids.py drop in without rescaling.
"""

from __future__ import annotations

from manim import Axes, ThreeDAxes

from theme import AXIS_GREEN, AXIS_RED


def plane_2d(
    x_range: tuple = (0, 5, 1),
    y_range: tuple = (0, 4, 1),
    x_length: float = 6.0,
    y_length: float = 6.0,
) -> Axes:
    """2D axes with the reference red x-axis / green y-axis."""
    return Axes(
        x_range=list(x_range),
        y_range=list(y_range),
        x_length=x_length,
        y_length=y_length,
        x_axis_config={"color": AXIS_RED},
        y_axis_config={"color": AXIS_GREEN},
        tips=True,
    )


def axes_3d(
    x_range: tuple = (-1, 5, 1),
    y_range: tuple = (-3, 3, 1),
    z_range: tuple = (-3, 3, 1),
    x_length: float = 6.0,
    y_length: float = 6.0,
    z_length: float = 6.0,
) -> ThreeDAxes:
    """3D axes with a 1:1 data-to-scene mapping (matches solids.py raw coords)."""
    return ThreeDAxes(
        x_range=list(x_range),
        y_range=list(y_range),
        z_range=list(z_range),
        x_length=x_length,
        y_length=y_length,
        z_length=z_length,
    )
