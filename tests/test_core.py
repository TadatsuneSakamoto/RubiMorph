from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT_DIR / "src" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from rubimorph import (
    EmphasisToken,
    RenderOptions,
    RubyToken,
    convert_text,
    parse_to_tokens,
    target_uses_plain_ruby_mode,
)
from rubimorph.fileops import convert_directory, convert_file


class CoreConversionTests(unittest.TestCase):
    def test_kakuyomu_ruby_to_html(self) -> None:
        result = convert_text(
            "kakuyomu",
            "html",
            "これは｜禁猟の園《きんりょうのその》です。",
        )
        self.assertEqual(
            result.output,
            "これは<ruby>禁猟の園<rt>きんりょうのその</rt></ruby>です。",
        )

    def test_html_ruby_to_kakuyomu(self) -> None:
        result = convert_text(
            "html",
            "kakuyomu",
            "<ruby>親文字<rt>ルビ</rt></ruby>",
        )
        self.assertEqual(result.output, "｜親文字《ルビ》")

    def test_kakuyomu_ruby_to_pixiv(self) -> None:
        result = convert_text("kakuyomu", "pixiv", "｜漢字《かんじ》")
        self.assertEqual(result.output, "[[rb: 漢字 > かんじ]]")

    def test_pixiv_ruby_to_kakuyomu(self) -> None:
        result = convert_text("pixiv", "kakuyomu", "[[rb: pixiv > ピクシブ]]")
        self.assertEqual(result.output, "｜pixiv《ピクシブ》")

    def test_parentheses_ruby_to_kakuyomu(self) -> None:
        result = convert_text("narou", "kakuyomu", "山田太郎(やまだたろう)")
        self.assertEqual(result.output, "｜山田太郎《やまだたろう》")

    def test_emphasis_token(self) -> None:
        tokens = parse_to_tokens("kakuyomu", "ここは《《傍点》》です。")
        self.assertTrue(any(isinstance(token, EmphasisToken) for token in tokens))

    def test_kakuyomu_emphasis_to_pixiv(self) -> None:
        result = convert_text("kakuyomu", "pixiv", "《《重要》》")
        self.assertEqual(result.output, "[[emphasismark: 重要 > ﹅]]")

    def test_pixiv_emphasis_to_aozora(self) -> None:
        result = convert_text("pixiv", "aozora", "[[emphasismark: 重要 > •]]")
        self.assertEqual(result.output, "［＃「重要」に傍点］")

    def test_plain_output_removes_ruby(self) -> None:
        result = convert_text("kakuyomu", "plain", "｜親文字《ルビ》")
        self.assertEqual(result.output, "親文字")

    def test_plain_output_keeps_ruby_in_parentheses(self) -> None:
        result = convert_text(
            "kakuyomu",
            "plain",
            "｜親文字《ルビ》",
            RenderOptions(plain_ruby_mode="parentheses"),
        )
        self.assertEqual(result.output, "親文字（ルビ）")

    def test_plain_ruby_mode_applies_only_to_plain_renderer(self) -> None:
        self.assertTrue(target_uses_plain_ruby_mode("plain"))
        self.assertFalse(target_uses_plain_ruby_mode("html"))
        self.assertFalse(target_uses_plain_ruby_mode("kakuyomu"))
        self.assertFalse(target_uses_plain_ruby_mode("markdown"))

    def test_multiple_ruby_tokens_are_preserved(self) -> None:
        result = convert_text(
            "kakuyomu",
            "narou",
            "｜空《そら》と｜海《うみ》を見る。",
        )
        self.assertEqual(result.output, "｜空《そら》と｜海《うみ》を見る。")
        self.assertEqual(sum(isinstance(token, RubyToken) for token in result.tokens), 2)

    def test_unclosed_bracket_warning(self) -> None:
        result = convert_text("kakuyomu", "html", "これは《未閉じ")
        self.assertTrue(
            any(diagnostic.code == "unclosed_open_bracket" for diagnostic in result.diagnostics)
        )

    def test_unsupported_platform_warning(self) -> None:
        result = convert_text("alphapolis", "kakuyomu", "本文")
        self.assertTrue(
            any(diagnostic.code == "source_platform_not_supported" for diagnostic in result.diagnostics)
        )

    def test_utf8_japanese_text_is_preserved(self) -> None:
        source = "第一章\n彼女は｜黎明《れいめい》の街を歩いた。"
        result = convert_text("kakuyomu", "plain", source)
        self.assertIn("第一章", result.output)
        self.assertIn("彼女は黎明の街を歩いた。", result.output)


class FileConversionTests(unittest.TestCase):
    def test_single_file_conversion_does_not_overwrite_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "原稿.txt"
            source.write_text("｜空《そら》", encoding="utf-8")
            result = convert_file(source, source, "kakuyomu", "plain")
            self.assertEqual(source.read_text(encoding="utf-8"), "｜空《そら》")
            self.assertEqual(result.destination.name, "原稿_converted.txt")
            self.assertEqual(result.destination.read_text(encoding="utf-8"), "空")

    def test_directory_conversion_preserves_subfolders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "入力"
            output_dir = root / "出力"
            nested = input_dir / "章"
            nested.mkdir(parents=True)
            (nested / "一話.txt").write_text("｜海《うみ》", encoding="utf-8")
            results = convert_directory(input_dir, output_dir, "kakuyomu", "plain")
            self.assertEqual(len(results), 1)
            self.assertEqual((output_dir / "章" / "一話.txt").read_text(encoding="utf-8"), "海")


class CliTests(unittest.TestCase):
    def test_cli_version(self) -> None:
        expected_version = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()
        result = subprocess.run(
            [sys.executable, str(ROOT_DIR / "src" / "cli" / "rubimorph.py"), "--version"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertIn(f"RubiMorph {expected_version}", result.stdout)

    def test_cli_list_platforms(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT_DIR / "src" / "cli" / "rubimorph.py"), "--list-platforms"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertIn("pixiv", result.stdout)
        self.assertIn("kakuyomu", result.stdout)


class GuiMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location(
            "rubimorph_desktop_app_for_tests",
            ROOT_DIR / "src" / "desktop" / "app.py",
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load desktop app module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.app_module = module

    def test_about_links_are_current(self) -> None:
        self.assertEqual(
            [url for _label, url in self.app_module.ABOUT_LINKS],
            [
                "https://x.com/Tadatsune_S",
                "https://www.tadatsune.com/",
                "https://github.com/TadatsuneSakamoto",
                "https://github.com/TadatsuneSakamoto/RubiMorph",
            ],
        )

    def test_license_documents_resolve_from_source_tree(self) -> None:
        for _title, relative_path in self.app_module.LICENSE_DOCUMENTS:
            path = self.app_module._resource_path(relative_path)
            self.assertTrue(path.is_file(), path)


if __name__ == "__main__":
    unittest.main()
