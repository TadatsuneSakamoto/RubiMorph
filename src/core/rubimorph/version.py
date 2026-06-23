"""Version helpers for RubiMorph."""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "RubiMorph"


def get_version() -> str:
    """Read the project version from the repository-level VERSION file."""

    candidates: list[Path] = []
    pyinstaller_root = getattr(sys, "_MEIPASS", None)
    if pyinstaller_root:
        candidates.append(Path(pyinstaller_root) / "VERSION")

    module_path = Path(__file__).resolve()
    candidates.extend(
        [
            module_path.parents[3] / "VERSION",
            Path.cwd() / "VERSION",
        ]
    )

    for version_file in candidates:
        try:
            version = version_file.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if version:
            return version
    return "0.0.0"


__version__ = get_version()
