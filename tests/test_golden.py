from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT_DIR / "src" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from rubimorph import convert_text


class GoldenConversionTests(unittest.TestCase):
    def test_kakuyomu_to_pixiv_golden(self) -> None:
        case_dir = ROOT_DIR / "tests" / "golden" / "kakuyomu_to_pixiv"
        source = (case_dir / "input.txt").read_text(encoding="utf-8")
        expected = (case_dir / "expected.txt").read_text(encoding="utf-8")
        result = convert_text("kakuyomu", "pixiv", source)
        self.assertEqual(result.output, expected)


if __name__ == "__main__":
    unittest.main()
