from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT_DIR / "examples" / "custom-profiles"
WEB_DIR = ROOT_DIR / "src" / "web" / "public"
WEB_SAMPLE_DIR = WEB_DIR / "samples"


class WebAssetTests(unittest.TestCase):
    def test_web_pages_keep_document_roles_and_sample_links(self) -> None:
        guide = (WEB_DIR / "guide.html").read_text(encoding="utf-8")
        manual = (WEB_DIR / "manual.html").read_text(encoding="utf-8")

        self.assertIn("RubiMorph 1.0.0 使用ガイド", guide)
        self.assertIn("導入ガイド", guide)
        self.assertIn("/RubiMorph/manual.html#custom-sample", guide)
        self.assertIn("/RubiMorph/samples/RubiMorph_Custom_Profile_Samples.zip", guide)

        self.assertIn("RubiMorph 1.0.0 操作マニュアル", manual)
        self.assertIn("カスタム形式サンプルを試す", manual)
        self.assertIn("ルビ出力", manual)
        self.assertIn("ステータス、ログ、警告", manual)
        for name in [
            "example-bracket-format.rubimorph-profile.json",
            "example-input.txt",
            "example-expected-output.txt",
            "author-work-sample-kakuyomu.txt",
            "author-work-sample-custom-format.txt",
            "author-work-sample-roundtrip-kakuyomu.txt",
            "RubiMorph_Custom_Profile_Samples.zip",
        ]:
            self.assertIn(f"/RubiMorph/samples/{name}", manual)

    def test_web_samples_match_repository_samples(self) -> None:
        sample_names = [
            "README.txt",
            "example-bracket-format.rubimorph-profile.json",
            "example-input.txt",
            "example-expected-output.txt",
            "author-work-sample-kakuyomu.txt",
            "author-work-sample-custom-format.txt",
            "author-work-sample-roundtrip-kakuyomu.txt",
            "RubiMorph_Custom_Profile_Samples.zip",
        ]
        for name in sample_names:
            with self.subTest(name=name):
                self.assertEqual(
                    (WEB_SAMPLE_DIR / name).read_bytes(),
                    (EXAMPLE_DIR / name).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
