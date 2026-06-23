from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import unicodedata
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT_DIR / "src" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from rubimorph import (  # noqa: E402
    CustomFormatProfile,
    ProfileCapabilities,
    ProfileTimeoutError,
    convert_text_flexible,
    delete_registered_profile,
    export_registered_profile,
    import_profile_file,
    list_enabled_registered_profiles,
    load_registered_profiles,
    load_profile,
    register_profile,
    save_profile,
    set_registered_profile_enabled,
    validate_profile_collection,
    validate_profile_data,
    validate_profile_file,
)


SAMPLE_PROFILE = ROOT_DIR / "examples" / "custom-profiles" / "example-bracket-format.rubimorph-profile.json"
SAMPLE_DIR = SAMPLE_PROFILE.parent


def profile_data(**overrides):
    data = {
        "schema_version": 1,
        "profile_id": "test-format",
        "name": "テスト形式",
        "description": "日本語説明",
        "capabilities": {"input": True, "output": True},
        "parser": {
            "rules": [
                {
                    "id": "ruby",
                    "name": "ルビ",
                    "kind": "ruby",
                    "enabled": True,
                    "priority": 100,
                    "pattern": r"\[\[ruby:(?P<base>.+?)\|(?P<reading>.+?)\]\]",
                    "flags": [],
                },
                {
                    "id": "emphasis",
                    "name": "傍点",
                    "kind": "emphasis",
                    "enabled": True,
                    "priority": 90,
                    "pattern": r"\[\[em:(?P<text>.+?)\]\]",
                    "flags": [],
                },
            ]
        },
        "renderer": {
            "templates": {
                "ruby": "[[ruby:{base}|{reading}]]",
                "emphasis": "[[em:{text}]]",
            }
        },
        "transforms": {
            "before_parse": [],
            "after_render": [],
        },
    }
    data.update(overrides)
    return data


def write_profile(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class CustomProfileCoreTests(unittest.TestCase):
    def test_sample_profile_loads(self) -> None:
        profile = load_profile(SAMPLE_PROFILE)
        self.assertEqual(profile.profile_id, "example-bracket-format")
        self.assertTrue(profile.capabilities.input)
        self.assertTrue(profile.capabilities.output)

    def test_author_work_sample_roundtrip_is_generated_by_profile(self) -> None:
        profile = load_profile(SAMPLE_PROFILE)
        source = (SAMPLE_DIR / "author-work-sample-kakuyomu.txt").read_text(encoding="utf-8")
        expected_custom = (SAMPLE_DIR / "author-work-sample-custom-format.txt").read_text(encoding="utf-8")
        expected_roundtrip = (SAMPLE_DIR / "author-work-sample-roundtrip-kakuyomu.txt").read_text(encoding="utf-8")

        custom_result = convert_text_flexible(source, source_platform="kakuyomu", target_profile=profile)
        self.assertEqual(custom_result.output, expected_custom)

        roundtrip_result = convert_text_flexible(expected_custom, source_profile=profile, target_platform="kakuyomu")
        self.assertEqual(roundtrip_result.output, expected_roundtrip)
        self.assertEqual(expected_roundtrip, source)
        self.assertTrue(source.startswith("\u3000"))
        self.assertTrue(unicodedata.is_normalized("NFC", source))
        self.assertTrue(unicodedata.is_normalized("NFC", expected_custom))
        self.assertTrue(unicodedata.is_normalized("NFC", expected_roundtrip))
        self.assertEqual(expected_custom.count("[[ruby:"), 4)
        for base, reading in {
            "僻邑": "へきゆう",
            "暗晦": "あんかい",
            "蛍雪": "けいせつ",
            "黴菌": "ばいきん",
        }.items():
            self.assertIn(f"[[ruby:{base}|{reading}]]", expected_custom)

    def test_sample_zip_contains_ascii_filenames(self) -> None:
        expected = {
            "example-bracket-format.rubimorph-profile.json",
            "example-input.txt",
            "example-expected-output.txt",
            "author-work-sample-kakuyomu.txt",
            "author-work-sample-custom-format.txt",
            "author-work-sample-roundtrip-kakuyomu.txt",
            "README.txt",
        }
        with zipfile.ZipFile(SAMPLE_DIR / "RubiMorph_Custom_Profile_Samples.zip") as archive:
            names = set(archive.namelist())
        self.assertEqual(names, expected)
        for name in names:
            name.encode("ascii")

    def test_profile_save_and_reload_preserves_japanese(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jp.rubimorph-profile.json"
            profile = load_profile(SAMPLE_PROFILE)
            save_profile(
                CustomFormatProfile(
                    schema_version=1,
                    profile_id="jp-format",
                    name="日本語名",
                    description="日本語説明",
                    enabled=True,
                    capabilities=profile.capabilities,
                    parser_rules=profile.parser_rules,
                    renderer_templates=profile.renderer_templates,
                    before_parse=profile.before_parse,
                    after_render=profile.after_render,
                ),
                path,
            )
            loaded = load_profile(path)
            self.assertEqual(loaded.name, "日本語名")
            self.assertEqual(loaded.description, "日本語説明")

    def test_builtin_to_custom(self) -> None:
        custom = load_profile(SAMPLE_PROFILE)
        result = convert_text_flexible(
            "これは｜親文字《ルビ》と《《傍点》》です。",
            source_platform="kakuyomu",
            target_profile=custom,
        )
        self.assertEqual(result.output, "これは[[ruby:親文字|ルビ]]と[[em:傍点]]です。")

    def test_custom_to_builtin(self) -> None:
        custom = load_profile(SAMPLE_PROFILE)
        result = convert_text_flexible(
            "[[ruby:親文字|ルビ]]と[[em:傍点]]",
            source_profile=custom,
            target_platform="kakuyomu",
        )
        self.assertEqual(result.output, "｜親文字《ルビ》と《《傍点》》")

    def test_custom_to_custom(self) -> None:
        custom = load_profile(SAMPLE_PROFILE)
        result = convert_text_flexible(
            "前[[ruby:親文字|ルビ]]中[[em:傍点]]後",
            source_profile=custom,
            target_profile=custom,
        )
        self.assertEqual(result.output, "前[[ruby:親文字|ルビ]]中[[em:傍点]]後")

    def test_unmatched_text_is_preserved(self) -> None:
        custom = load_profile(SAMPLE_PROFILE)
        result = convert_text_flexible(
            "未一致 [[ruby:空|そら]] end",
            source_profile=custom,
            target_platform="plain",
        )
        self.assertEqual(result.output, "未一致 空 end")

    def test_priority_start_length_and_definition_order(self) -> None:
        data = profile_data()
        data["parser"]["rules"] = [
            {
                "id": "low",
                "name": "低優先",
                "kind": "emphasis",
                "enabled": True,
                "priority": 1,
                "pattern": r"(?P<text>A)",
                "flags": [],
            },
            {
                "id": "high",
                "name": "高優先",
                "kind": "emphasis",
                "enabled": True,
                "priority": 10,
                "pattern": r"(?P<text>A)",
                "flags": [],
            },
            {
                "id": "long",
                "name": "長い一致",
                "kind": "emphasis",
                "enabled": True,
                "priority": 5,
                "pattern": r"(?P<text>AB)",
                "flags": [],
            },
            {
                "id": "same_first",
                "name": "同順1",
                "kind": "emphasis",
                "enabled": True,
                "priority": 3,
                "pattern": r"(?P<text>B)",
                "flags": [],
            },
            {
                "id": "same_second",
                "name": "同順2",
                "kind": "emphasis",
                "enabled": True,
                "priority": 3,
                "pattern": r"(?P<text>B)",
                "flags": [],
            },
        ]
        data["renderer"]["templates"]["emphasis"] = "<{text}>"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "priority.rubimorph-profile.json"
            write_profile(path, data)
            profile = load_profile(path)
            result = convert_text_flexible("CAB", source_profile=profile, target_profile=profile)
            self.assertEqual(result.output, "C<A><B>")

    def test_longer_match_wins_when_start_and_priority_equal(self) -> None:
        data = profile_data()
        data["parser"]["rules"] = [
            {
                "id": "short",
                "name": "短い",
                "kind": "emphasis",
                "enabled": True,
                "priority": 10,
                "pattern": r"(?P<text>A)",
                "flags": [],
            },
            {
                "id": "long",
                "name": "長い",
                "kind": "emphasis",
                "enabled": True,
                "priority": 10,
                "pattern": r"(?P<text>AB)",
                "flags": [],
            },
        ]
        data["renderer"]["templates"]["emphasis"] = "<{text}>"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "long.rubimorph-profile.json"
            write_profile(path, data)
            profile = load_profile(path)
            result = convert_text_flexible("AB", source_profile=profile, target_profile=profile)
            self.assertEqual(result.output, "<AB>")

    def test_before_after_literal_regex_and_disabled_rule(self) -> None:
        data = profile_data()
        data["parser"]["rules"].append(
            {
                "id": "disabled",
                "name": "無効",
                "kind": "emphasis",
                "enabled": False,
                "priority": 200,
                "pattern": r"(?P<text>DISABLED)",
                "flags": [],
            }
        )
        data["transforms"] = {
            "before_parse": [
                {
                    "id": "literal",
                    "name": "literal",
                    "enabled": True,
                    "type": "literal",
                    "pattern": "[[rb:",
                    "replacement": "[[ruby:",
                    "flags": [],
                }
            ],
            "after_render": [
                {
                    "id": "regex",
                    "name": "regex",
                    "enabled": True,
                    "type": "regex",
                    "pattern": r"\s{2,}",
                    "replacement": " ",
                    "flags": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transforms.rubimorph-profile.json"
            write_profile(path, data)
            profile = load_profile(path)
            result = convert_text_flexible(
                "[[rb:空|そら]]  DISABLED",
                source_profile=profile,
                target_profile=profile,
            )
            self.assertEqual(result.output, "[[ruby:空|そら]] DISABLED")

    def test_profile_collection_duplicate_id(self) -> None:
        profile = CustomFormatProfile(
            schema_version=1,
            profile_id="dup",
            name="dup",
            description="",
            enabled=True,
            capabilities=ProfileCapabilities(True, True),
        )
        result = validate_profile_collection([profile, profile])
        self.assertFalse(result.is_valid)
        self.assertIn("重複", result.errors[0].message)

    def test_registered_profile_api_import_export_enable_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = load_profile(SAMPLE_PROFILE)
            path = register_profile(profile, tmp)
            self.assertTrue(path.is_file())

            records = load_registered_profiles(tmp)
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0].validation.is_valid)
            self.assertEqual(
                [item.profile_id for item in list_enabled_registered_profiles(tmp)],
                [profile.profile_id],
            )

            set_registered_profile_enabled(profile.profile_id, False, tmp)
            self.assertEqual(list_enabled_registered_profiles(tmp), [])

            export_dir = Path(tmp) / "exports"
            export_dir.mkdir()
            exported = export_dir / "exported.rubimorph-profile.json"
            export_registered_profile(profile.profile_id, exported, tmp)
            self.assertTrue(exported.is_file())

            delete_registered_profile(profile.profile_id, tmp)
            self.assertEqual(load_registered_profiles(tmp), [])
            import_profile_file(exported, tmp)
            self.assertEqual(len(load_registered_profiles(tmp)), 1)

    def test_timeout_wrapper_stops_custom_conversion(self) -> None:
        custom = load_profile(SAMPLE_PROFILE)
        with self.assertRaises(ProfileTimeoutError):
            convert_text_flexible(
                "[[ruby:親|よみ]]",
                source_profile=custom,
                target_platform="plain",
                timeout_seconds=0.0,
            )


class CustomProfileValidationTests(unittest.TestCase):
    def assertInvalid(self, data: dict, expected: str) -> None:
        result = validate_profile_data(data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any(expected in issue.message or expected in issue.path for issue in result.errors))

    def test_broken_json_and_non_utf8_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.rubimorph-profile.json"
            broken.write_text("{", encoding="utf-8")
            self.assertFalse(validate_profile_file(broken).is_valid)
            non_utf8 = Path(tmp) / "non_utf8.rubimorph-profile.json"
            non_utf8.write_bytes(b"\xff\xfe\x00")
            self.assertFalse(validate_profile_file(non_utf8).is_valid)

    def test_validation_errors(self) -> None:
        cases = [
            ({"schema_version": 2}, "schema_version"),
            (profile_data(profile_id="bad id"), "profile_id"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "id": "x"}, {**profile_data()["parser"]["rules"][0], "id": "x"}]}), "重複"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "pattern": "["}]}), "コンパイル"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "pattern": ""}]}), "空"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "pattern": r"(?P<base>.*)(?P<reading>.*)"}]}), "ゼロ文字"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "pattern": r"(?P<base>.+)"}]}), "名前付きグループ"),
            (profile_data(renderer={"templates": {"ruby": "{base.__class__}"}}), "プレースホルダー"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "kind": "unknown"}]}), "kind"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "flags": ["BAD"]}]}), "flags"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "priority": "high"}]}), "priority"),
            (profile_data(extra=True), "不明"),
            (profile_data(parser={"rules": [profile_data()["parser"]["rules"][0]] * 101}), "規則数"),
            (profile_data(parser={"rules": [{**profile_data()["parser"]["rules"][0], "pattern": "a" * 513}]}), "パターン長"),
            (profile_data(renderer={"templates": {"ruby": "a" * 513}}), "テンプレート長"),
        ]
        for data, expected in cases:
            with self.subTest(expected=expected):
                self.assertInvalid(data, expected)

    def test_top_level_must_be_object_and_file_size_limit(self) -> None:
        self.assertFalse(validate_profile_data([]).is_valid)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "huge.rubimorph-profile.json"
            path.write_text(" " * (256 * 1024 + 1), encoding="utf-8")
            self.assertFalse(validate_profile_file(path).is_valid)


class CustomProfileCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT_DIR / "src" / "cli" / "rubimorph.py"), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_cli_validate_profile(self) -> None:
        result = self.run_cli("--validate-profile", str(SAMPLE_PROFILE))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[OK]", result.stdout)

    def test_cli_from_profile(self) -> None:
        result = self.run_cli(
            "--from-profile",
            str(SAMPLE_PROFILE),
            "--to",
            "plain",
            "--text",
            "[[ruby:空|そら]]",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "空")

    def test_cli_to_profile(self) -> None:
        result = self.run_cli(
            "--from",
            "kakuyomu",
            "--to-profile",
            str(SAMPLE_PROFILE),
            "--text",
            "｜空《そら》",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[[ruby:空|そら]]")

    def test_cli_custom_to_custom(self) -> None:
        result = self.run_cli(
            "--from-profile",
            str(SAMPLE_PROFILE),
            "--to-profile",
            str(SAMPLE_PROFILE),
            "--text",
            "[[em:重要]]",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[[em:重要]]")

    def test_cli_rejects_conflicting_options(self) -> None:
        from_result = self.run_cli(
            "--from",
            "kakuyomu",
            "--from-profile",
            str(SAMPLE_PROFILE),
            "--to",
            "plain",
            "--text",
            "x",
        )
        self.assertNotEqual(from_result.returncode, 0)
        to_result = self.run_cli(
            "--from",
            "kakuyomu",
            "--to",
            "plain",
            "--to-profile",
            str(SAMPLE_PROFILE),
            "--text",
            "x",
        )
        self.assertNotEqual(to_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
