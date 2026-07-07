"""VidMak pipeline entrypoint.

    python pipeline/run.py --topic "Khối tròn xoay"

Phase 1 in progress: runs Analysis -> Storyboard -> Script so far, writing
projects/<slug>/{analysis.md, storyboard.json, script.json}. The remaining
layers (codegen -> assembly) get wired in here as they land -- see PLAN.md.
"""

from __future__ import annotations

import argparse
import sys

from agents.analysis import run_analysis
from agents.script import run_script
from agents.storyboard import run_storyboard
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
    args = parser.parse_args(argv)

    slug = slugify(args.topic)

    print(f"[1/3] Analysis:   {args.topic}  ->  projects/{slug}/")
    analysis_path = run_analysis(args.topic)
    print(f"  OK  {analysis_path.relative_to(REPO_ROOT)}")

    print(f"[2/3] Storyboard: {args.topic}")
    storyboard_path = run_storyboard(args.topic)
    print(f"  OK  {storyboard_path.relative_to(REPO_ROOT)}")

    print(f"[3/3] Script:     {args.topic}")
    script_path = run_script(args.topic)
    print(f"  OK  {script_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
