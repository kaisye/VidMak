"""VidMak pipeline entrypoint.

    python pipeline/run.py --topic "Khối tròn xoay"

Phase 1: runs the whole chain Analysis -> Storyboard -> Script -> Codegen ->
Render -> Assembly, writing projects/<slug>/{analysis.md, storyboard.json,
script.json, scenes/*.py, media/**/*.mp4, output/final.mp4}.
"""

from __future__ import annotations

import argparse
import sys

from agents.analysis import run_analysis
from agents.codegen import run_codegen
from agents.script import run_script
from agents.storyboard import run_storyboard
from assemble import run_assembly
from render import render_project
from workspace import REPO_ROOT, slugify


def main(argv: list[str] | None = None) -> int:
    # The topic and paths are Vietnamese; force utf-8 so printing them does not
    # crash on the legacy Windows console code page.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        prog="vidmak", description="Sinh video Manim từ một chủ đề học thuật."
    )
    parser.add_argument("--topic", required=True, help='Chủ đề, vd: "Khối tròn xoay"')
    parser.add_argument(
        "--draft", action="store_true",
        help="Render nhanh ở độ phân giải thấp (360x640@15) thay vì full-res.",
    )
    parser.add_argument(
        "--workers", type=int, default=4,
        help="Số cảnh render song song (mặc định 4).",
    )
    args = parser.parse_args(argv)

    slug = slugify(args.topic)

    print(f"[1/6] Analysis:   {args.topic}  ->  projects/{slug}/")
    analysis_path = run_analysis(args.topic)
    print(f"  OK  {analysis_path.relative_to(REPO_ROOT)}")

    print(f"[2/6] Storyboard: {args.topic}")
    storyboard_path = run_storyboard(args.topic)
    print(f"  OK  {storyboard_path.relative_to(REPO_ROOT)}")

    print(f"[3/6] Script:     {args.topic}")
    script_path = run_script(args.topic)
    print(f"  OK  {script_path.relative_to(REPO_ROOT)}")

    print(f"[4/6] Codegen:    {args.topic}")
    specs = run_codegen(args.topic)
    print(f"  OK  {len(specs)} cảnh -> projects/{slug}/scenes/")

    print(f"[5/6] Render:     {args.topic}  (workers={args.workers}, {'draft' if args.draft else 'full-res'})")
    clips = render_project(args.topic, draft=args.draft, workers=args.workers)
    fallbacks = sum(1 for c in clips if c["fallback"])
    note = f" ({fallbacks} cảnh tối giản)" if fallbacks else ""
    print(f"  OK  {len(clips)} clip -> projects/{slug}/media/{note}")

    print(f"[6/6] Assembly:   {args.topic}")
    final = run_assembly(args.topic, draft=args.draft)
    print(f"  OK  {final.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
