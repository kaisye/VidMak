"""Layer 4c -- Assembly.

Concatenates the per-scene clips (projects/<slug>/media/videos/<id>/.../<Class>.mp4,
written by the render layer) into projects/<slug>/output/final.mp4, in storyboard
order, with the narration audio preserved.

Uses ffmpeg's concat FILTER (re-encode) rather than the concat demuxer: the clips
all share codec/size/fps, but re-encoding is cheap for ~90s of 720x1280 and makes
the join robust to tiny timestamp/audio-rate differences between clips. Every clip
must carry an audio stream -- a silent clip means a scene lost its voiceover
(see codegen's anti-stub guard), which we surface loudly rather than paper over.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from agents.codegen import scene_specs
from render import FULL_QUALITY_DIR, DRAFT_QUALITY_DIR
from workspace import project_dir


def _clip_path(media_dir: Path, scene_id: str, class_name: str, *, draft: bool) -> Path | None:
    quality = DRAFT_QUALITY_DIR if draft else FULL_QUALITY_DIR
    out = media_dir / "videos" / scene_id / quality / f"{class_name}.mp4"
    return out if out.exists() else None


def _has_audio(clip: Path) -> bool:
    """True if ffprobe sees an audio stream (a scene with no narration is a bug)."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(clip)],
        capture_output=True, text=True,
    )
    return "audio" in (proc.stdout or "")


def run_assembly(topic: str, *, draft: bool = False) -> Path:
    """Join every scene clip of `topic` into output/final.mp4; return its path."""
    proj = project_dir(topic)
    media_dir = proj / "media"

    clips: list[Path] = []
    missing: list[str] = []
    silent: list[str] = []
    for spec in scene_specs(topic):
        clip = _clip_path(media_dir, spec["id"], spec["class"], draft=draft)
        if clip is None:
            missing.append(spec["id"])
            continue
        if not _has_audio(clip):
            silent.append(spec["id"])
        clips.append(clip)

    if missing:
        raise FileNotFoundError(
            "Chưa render đủ cảnh, thiếu: " + ", ".join(missing) + " (chạy tầng Render trước)."
        )
    if silent:
        raise ValueError(
            "Cảnh không có audio (mất thoại): " + ", ".join(silent) +
            " — render lại cảnh đó (kiểm tra voiceover) trước khi ghép."
        )

    out_dir = proj / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / "final.mp4"

    cmd: list[str] = ["ffmpeg", "-v", "error", "-y"]
    for clip in clips:
        cmd += ["-i", str(clip)]
    streams = "".join(f"[{i}:v][{i}:a]" for i in range(len(clips)))
    cmd += [
        "-filter_complex", f"{streams}concat=n={len(clips)}:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        str(final),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg ghép thất bại:\n" + (proc.stderr or "")[-2000:])
    return final


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ghép các cảnh thành final.mp4")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--draft", action="store_true", help="Ghép bản draft thay vì full-res")
    args = parser.parse_args()
    print(run_assembly(args.topic, draft=args.draft))
