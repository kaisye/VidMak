"""Project workspace layout.

Each topic gets its own folder projects/<slug>/ holding the whole artifact
chain (analysis.md -> storyboard.json -> script.json -> scenes/ -> output/).
See ARCHITECTURE.md for the folder contract. This module owns two things:
turning a Vietnamese topic into a stable ascii folder slug, and resolving the
project directory.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Repo root is the parent of pipeline/. Kept relative to this file so the CLI
# works regardless of the caller's current directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"


def slugify(topic: str) -> str:
    """Vietnamese topic -> ascii folder slug.

    'Khối tròn xoay' -> 'khoi-tron-xoay'. Strips diacritics via NFD (so 'ố'
    becomes 'o'), maps the standalone letter 'đ' -> 'd' (it does not decompose
    under NFD), then collapses everything else to hyphens.
    """
    normalized = unicodedata.normalize("NFD", topic.lower())
    ascii_str = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    ascii_str = ascii_str.replace("đ", "d")
    ascii_str = re.sub(r"[^a-z0-9]+", "-", ascii_str).strip("-")
    return ascii_str or "topic"


def project_dir(topic: str, *, create: bool = True) -> Path:
    """Return projects/<slug>/ for `topic`, creating it by default."""
    d = PROJECTS_DIR / slugify(topic)
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d
