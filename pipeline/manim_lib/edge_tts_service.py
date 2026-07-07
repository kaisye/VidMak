"""Custom SpeechService adapter wrapping the `edge-tts` package.

manim-voiceover 0.4.0 dropped the built-in EdgeTTSService that older
tutorials reference -- the installed version only ships azure, elevenlabs,
gemini, gtts, openai, pyttsx3, recorder under `manim_voiceover.services`.
This mirrors GTTSService (the simplest built-in service) against the
current SpeechService interface. See DECISIONS.md D008.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from manim_voiceover._typing import VoiceoverData
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import (
    PathLike,
    SpeechService,
    initialize_speech_service,
    path_to_string,
)


class EdgeTTSService(SpeechService):
    """SpeechService wrapper for Microsoft Edge's online neural TTS voices."""

    def __init__(
        self,
        voice: str = "vi-VN-HoaiMyNeural",
        rate: str = "+0%",
        **kwargs: object,
    ) -> None:
        initialize_speech_service(self, kwargs)
        self.voice = voice
        self.rate = rate

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "edge-tts",
            "voice": self.voice,
            "rate": self.rate,
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path_to_string(path)

        full_path = str(Path(cache_dir) / audio_path)
        communicate = edge_tts.Communicate(input_text, voice=self.voice, rate=self.rate)
        asyncio.run(communicate.save(full_path))

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }
