"""VidMak pipeline entrypoint.

    python pipeline/run.py --topic "Khối tròn xoay"

Phase 1 in progress: currently runs the Analysis layer only, writing
projects/<slug>/analysis.md. The remaining layers (storyboard -> script ->
codegen -> assembly) get wired in here as they land -- see PLAN.md.
"""

from __future__ import annotations

import argparse
import sys

from agents.analysis import run_analysis
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

    print(f"[1/1] Analysis: {args.topic}  ->  projects/{slugify(args.topic)}/")
    path = run_analysis(args.topic)
    print(f"  OK  {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
