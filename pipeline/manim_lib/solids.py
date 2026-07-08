"""Reusable 3D solids of revolution around the x-axis.

The heart of a "khối tròn xoay" video: turning a profile curve y=f(x) into the
solid it sweeps out, and the thin-disk Riemann picture behind the volume
integral. Codegen (layer 4) composes these instead of writing Surface math by
hand. Everything is built in raw scene coordinates (1 data unit = 1 scene unit)
so it lines up with axes.axes_3d's default 1:1 ranges.

Colors follow DESIGN.md B: cyan checkerboard body, thin gold edge.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from manim import RIGHT, TAU, Cylinder, ManimColor, Surface, VGroup

from theme import CURVE_CYAN, GOLD_ACCENT

# Two-tone cyan for the checkerboard shading that reads as a curved 3D surface.
_CHECKER = [CURVE_CYAN, ManimColor("#3A94AB")]


def lathe_from_curve(
    func: Callable[[float], float],
    x_range: tuple[float, float],
    resolution: tuple[int, int] = (24, 32),
) -> Surface:
    """Surface of revolution of y=func(x) spun a full turn around the x-axis."""
    a, b = x_range[0], x_range[1]

    def param(u: float, v: float) -> np.ndarray:
        r = func(u)
        return np.array([u, r * np.cos(v), r * np.sin(v)])

    return Surface(
        param,
        u_range=[a, b],
        v_range=[0, TAU],
        resolution=resolution,
        checkerboard_colors=_CHECKER,
        fill_opacity=0.7,
        stroke_color=GOLD_ACCENT,
        stroke_width=0.5,
    )


def disk_from_rect(
    radius: float, x_center: float = 0.0, thickness: float = 0.2
) -> Cylinder:
    """One thin disk (a short cylinder) of the given radius, centered at x_center.

    This is the disk a thin rectangle of height f(x) sweeps into when it rotates
    around the x-axis -- the atom of the volume integral.
    """
    disk = Cylinder(
        radius=max(radius, 1e-3),
        height=thickness,
        direction=RIGHT,
        checkerboard_colors=_CHECKER,
        fill_opacity=0.7,
        stroke_color=GOLD_ACCENT,
        stroke_width=0.5,
    )
    disk.move_to([x_center, 0, 0])
    return disk


def cylinder_stack(
    func: Callable[[float], float],
    x_range: tuple[float, float],
    n: int = 12,
) -> VGroup:
    """Riemann stack: n thin disks whose radii follow func across x_range."""
    a, b = x_range[0], x_range[1]
    dx = (b - a) / n
    disks = VGroup()
    for i in range(n):
        x_center = a + (i + 0.5) * dx
        disks.add(disk_from_rect(func(x_center), x_center=x_center, thickness=dx * 0.9))
    return disks
