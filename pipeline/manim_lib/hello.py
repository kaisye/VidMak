"""Phase 0 sanity-check scene: Vietnamese title + formula + synced voice.

Confirms the toolchain works end to end (Manim, Pango/Vietnamese text,
MathTex/LaTeX, manim-voiceover + edge-tts) before any pipeline code is built
on top of it. Not part of the generated-video pipeline itself.

Run: manim render -ql pipeline/manim_lib/hello.py HelloScene
"""

from manim import DOWN, Write
from manim_voiceover import VoiceoverScene

from edge_tts_service import EdgeTTSService
from theme import GOLD_ACCENT, CURVE_CYAN, configure, formula, vn_text

configure()


class HelloScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(EdgeTTSService(voice="vi-VN-HoaiMyNeural"))

        title = vn_text("Khối Tròn Xoay", color=GOLD_ACCENT).scale(1.1)
        eq = formula(r"V = \pi \int_a^b [f(x)]^2\,dx", color=CURVE_CYAN).next_to(
            title, DOWN, buff=0.8
        )

        with self.voiceover(
            text=(
                "Chào mừng đến với Vi Đi Mắc, nơi mọi khái niệm toán học "
                "được nhìn thấy bằng hình học."
            )
        ) as tracker:
            self.play(Write(title), run_time=tracker.duration * 0.45)
            self.play(Write(eq), run_time=tracker.duration * 0.55)

        self.wait(1)
