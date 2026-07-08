"""Smoke test for the manim_lib helper library (not part of the pipeline).

Two scenes that exercise every helper the storyboard references, proving they
construct and render before the codegen agent (layer 4b) relies on them. Like
hello.py, this is a toolchain check, not a generated video.

Run (media goes to a throwaway dir so it never lands in the repo):
  manim render -ql --media_dir <tmp> pipeline/manim_lib/smoke.py ComponentsSmoke
  manim render -ql --media_dir <tmp> pipeline/manim_lib/smoke.py SolidsSmoke
"""

from manim import (
    DEGREES,
    DOWN,
    UP,
    Create,
    FadeIn,
    FadeOut,
    Scene,
    ThreeDScene,
    VGroup,
    Write,
)

from axes import axes_3d, plane_2d
from components import brace_label, caption, end_card, formula_box, title_card
from solids import cylinder_stack, disk_from_rect, lathe_from_curve
from theme import CURVE_CYAN, configure, formula

configure()


class ComponentsSmoke(Scene):
    """2D overlays: title_card, plane_2d, formula_box, brace_label, caption, end_card."""

    def construct(self):
        title = title_card("Khối Tròn Xoay", "khi hình phẳng quét thành không gian")
        title.to_edge(UP, buff=1.3)
        self.play(Write(title))

        ax = plane_2d(x_range=(0, 5, 1), y_range=(0, 4, 1)).scale(0.7).move_to([0, 0.6, 0])
        curve = ax.plot(lambda x: 0.4 * x + 0.6, x_range=[0, 4], color=CURVE_CYAN)
        self.play(Create(ax), Create(curve))

        bl = brace_label(curve, "đường sinh f(x)", direction=UP)
        self.play(FadeIn(bl))

        fb = formula_box(formula(r"V = \pi \int_a^b [f(x)]^2\,dx", color=CURVE_CYAN))
        fb.scale(0.7).next_to(ax, DOWN, buff=0.5)
        self.play(Write(fb))

        cap = caption("Chiều cao trở thành bán kính")
        self.play(FadeIn(cap))
        self.wait(0.5)

        self.play(FadeOut(VGroup(title, ax, curve, bl, fb, cap)))
        ec = end_card(
            [
                "HỌC TIẾP: TÍCH PHÂN THỂ TÍCH",
                "NHÌN LÁT CẮT, THẤY KHỐI 3D",
                "THEO DÕI ĐỂ XEM BÀI TIẾP",
            ]
        ).scale(0.6)
        self.play(FadeIn(ec))
        self.wait(0.5)


class SolidsSmoke(ThreeDScene):
    """3D solids: axes_3d, lathe_from_curve, cylinder_stack, disk_from_rect."""

    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES)

        ax3 = axes_3d()
        self.play(Create(ax3))

        profile = lambda x: 0.4 * x + 0.5  # noqa: E731 -- terse profile for the smoke test
        surface = lathe_from_curve(profile, x_range=(0, 4))
        self.play(Create(surface))
        self.wait(0.3)

        self.play(FadeOut(surface))
        stack = cylinder_stack(profile, x_range=(0, 4), n=10)
        self.play(FadeIn(stack))
        self.wait(0.3)

        disk = disk_from_rect(1.4, x_center=2.0, thickness=0.35)
        self.play(FadeIn(disk))
        self.wait(0.5)
