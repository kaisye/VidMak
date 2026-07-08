"""Layer 4b -- Render with self-repair.

Turns each projects/<slug>/scenes/<id>.py into a clip by running the manim CLI,
and when a render fails it feeds the error back to the codegen agent, applies the
fix, and retries -- up to 4 rounds (ARCHITECTURE.md: "vòng 1 sửa lỗi render").
After 4 failed rounds it drops in a minimal fallback scene so the pipeline always
produces a clip for every beat.

Manim runs as a subprocess (a fresh interpreter) so a scene that hard-crashes the
process can't take the pipeline down with it. manim_lib is put on the subprocess
PYTHONPATH so the generated scenes' flat imports (`from theme import ...`) resolve
from the projects/<slug>/scenes/ directory (DECISIONS.md D010).
"""

from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agents.codegen import (
    fallback_scene_code,
    inject_narration,
    repair_scene,
    scene_specs,
    validate_scene_code,
    write_scene,
)
from workspace import REPO_ROOT, project_dir

MANIM_LIB_DIR = REPO_ROOT / "pipeline" / "manim_lib"
MAX_REPAIR_ROUNDS = 4


def _manim_env(draft: bool) -> dict:
    """Environment for the manim subprocess: manim_lib on PYTHONPATH, utf-8 IO.

    In draft mode set VIDMAK_DRAFT so theme.configure() picks the fast low-res
    frame config (the render/repair loop uses this; the final pass sets draft=False).
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(MANIM_LIB_DIR), env.get("PYTHONPATH", "")) if p
    )
    env["PYTHONIOENCODING"] = "utf-8"
    env["VIDMAK_DRAFT"] = "1" if draft else "0"
    # Keep each render single-threaded so N parallel scene renders share the cores
    # cleanly instead of every process spawning a BLAS thread pool and oversubscribing.
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[var] = "1"
    return env


def _run_manim(
    scene_file: Path,
    class_name: str,
    media_dir: Path,
    *,
    draft: bool = True,
    quality: str = "l",
) -> subprocess.CompletedProcess:
    """Render one scene via `python -m manim`; capture stdout/stderr, never raise."""
    cmd = [
        sys.executable,
        "-m",
        "manim",
        "render",
        f"-q{quality}",
        "--media_dir",
        str(media_dir),
        str(scene_file),
        class_name,
    ]
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=_manim_env(draft),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


# Manim's output quality folders for our frame configs: "<pixel_height>p<fps>".
# Mirrors theme.py (VIDEO_HEIGHT/FPS and DRAFT_HEIGHT/DRAFT_FPS) -- kept as plain
# strings here so the orchestrator never has to import manim just to build a path.
FULL_QUALITY_DIR = "1280p30"
DRAFT_QUALITY_DIR = "640p15"


def _quality_dirname(draft: bool) -> str:
    return DRAFT_QUALITY_DIR if draft else FULL_QUALITY_DIR


def _find_output(
    media_dir: Path, scene_file: Path, class_name: str, *, draft: bool
) -> Path | None:
    """Locate the rendered mp4 for the requested quality (draft vs full-res).

    Quality-scoped on purpose: a leftover draft mp4 must never be mistaken for
    the full-res result (or vice versa).
    """
    out = media_dir / "videos" / scene_file.stem / _quality_dirname(draft) / f"{class_name}.mp4"
    return out if out.exists() else None


def _distill_error(proc: subprocess.CompletedProcess) -> str:
    """Trim manim's output to the part worth sending back to the model.

    Prefer the tail from the last traceback; otherwise the last lines of output.
    Capped so the repair prompt stays lean.
    """
    blob = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()
    if not blob:
        return f"manim thoát với mã {proc.returncode} nhưng không in ra lỗi."
    marker = blob.rfind("Traceback (most recent call last)")
    if marker != -1:
        blob = blob[marker:]
    else:
        blob = "\n".join(blob.splitlines()[-40:])
    return blob[-3000:]


def render_scene_with_repair(
    spec: dict,
    media_dir: Path,
    *,
    draft: bool = True,
    max_rounds: int = MAX_REPAIR_ROUNDS,
) -> dict:
    """Render one scene, repairing on failure up to max_rounds, else falling back.

    Returns {id, class, mp4, rounds, fallback}. Raises only if even the minimal
    fallback scene will not render (a broken toolchain, not a bad scene).
    """
    scene_file: Path = spec["file"]
    class_name: str = spec["class"]

    for attempt in range(max_rounds + 1):
        # Static-check first: never spend a render on (or accept) code that a prior
        # repair "cheated" into passing -- e.g. a stubbed/silent voiceover renders
        # fine but ships a scene with no narration. Fix it instead of rendering it.
        problems = validate_scene_code(scene_file.read_text(encoding="utf-8"), class_name)
        if problems:
            error = "Lỗi kiểm tra tĩnh:\n- " + "\n- ".join(problems)
        else:
            proc = _run_manim(scene_file, class_name, media_dir, draft=draft)
            if proc.returncode == 0:
                out = _find_output(media_dir, scene_file, class_name, draft=draft)
                if out is not None:
                    return {
                        "id": spec["id"],
                        "class": class_name,
                        "mp4": out,
                        "rounds": attempt,
                        "fallback": False,
                    }
                error = "manim báo thành công nhưng không tìm thấy file mp4 xuất ra."
            else:
                error = _distill_error(proc)

        if attempt >= max_rounds:
            break
        print(f"    sửa lỗi vòng {attempt + 1}/{max_rounds}: {class_name}")
        fixed = repair_scene(scene_file.read_text(encoding="utf-8"), error, spec)
        scene_file.write_text(fixed, encoding="utf-8")

    print(f"    quá {max_rounds} vòng -> dùng cảnh tối giản: {class_name}")
    scene_file.write_text(fallback_scene_code(spec), encoding="utf-8")
    proc = _run_manim(scene_file, class_name, media_dir, draft=draft)
    if proc.returncode == 0:
        out = _find_output(media_dir, scene_file, class_name, draft=draft)
        if out is not None:
            return {
                "id": spec["id"],
                "class": class_name,
                "mp4": out,
                "rounds": max_rounds,
                "fallback": True,
            }
    raise RuntimeError(
        f"Không render được cảnh {class_name} kể cả bản tối giản:\n"
        + _distill_error(proc)
    )


def _prepare_scene_file(spec: dict, *, generate_missing: bool) -> None:
    """Make sure spec['file'] exists and its NARRATION is the canonical script text."""
    if not spec["file"].exists():
        if not generate_missing:
            raise FileNotFoundError(f"Thiếu {spec['file'].name}; chạy tầng Codegen trước.")
        print(f"  gen  {spec['id']} (thiếu, sinh bù)")
        write_scene(spec)
    else:
        spec["file"].write_text(
            inject_narration(spec["file"].read_text(encoding="utf-8"), spec["narration"]),
            encoding="utf-8",
        )


def render_project(
    topic: str, *, draft: bool = True, generate_missing: bool = True, workers: int = 1
) -> list[dict]:
    """Render every scene of `topic` (self-repair per scene). Returns clip results.

    Scenes are independent, so with workers>1 they render in parallel (each manim
    render is a single-threaded subprocess, so N workers use N cores). draft=True
    (default) renders the fast low-res draft; the final pass uses draft=False.
    """
    proj = project_dir(topic)
    media_dir = proj / "media"
    specs = scene_specs(topic)
    for spec in specs:
        _prepare_scene_file(spec, generate_missing=generate_missing)

    def _one(spec: dict) -> dict:
        print(f"  render {spec['id']}", flush=True)
        res = render_scene_with_repair(spec, media_dir, draft=draft)
        tag = " (tối giản)" if res["fallback"] else (f" ({res['rounds']} vòng sửa)" if res["rounds"] else "")
        print(f"    OK  {res['mp4'].relative_to(REPO_ROOT)}{tag}", flush=True)
        return res

    if workers <= 1:
        return [_one(spec) for spec in specs]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        # Preserve storyboard order in the returned list regardless of finish order.
        return list(pool.map(_one, specs))
