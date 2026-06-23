"""Source entry point for the RubiMorph CLI."""

from __future__ import annotations

import sys
from multiprocessing import freeze_support
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = ROOT_DIR / "src" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from rubimorph.cli import main  # noqa: E402


if __name__ == "__main__":
    freeze_support()
    raise SystemExit(main())
