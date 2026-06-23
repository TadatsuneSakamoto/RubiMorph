r"""Compatibility CLI entry point for RubiMorph.

Use src\cli\rubimorph.py for the primary CLI. This wrapper is kept so older
scripts that call nmc.py continue to work.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

CLI_PATH = Path(__file__).resolve().with_name("rubimorph.py")
SPEC = importlib.util.spec_from_file_location("rubimorph_cli", CLI_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load RubiMorph CLI: {CLI_PATH}")
_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(_module)
main = _module.main


if __name__ == "__main__":
    raise SystemExit(main())
