from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT_DIR / "src" / "core"
DESKTOP_DIR = ROOT_DIR / "src" / "desktop"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))
if str(DESKTOP_DIR) not in sys.path:
    sys.path.insert(0, str(DESKTOP_DIR))


def load_app_module():
    spec = importlib.util.spec_from_file_location(
        "rubimorph_desktop_app_gui_tests",
        ROOT_DIR / "src" / "desktop" / "app.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load desktop app module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GuiAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app_module = load_app_module()

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = str(Path(self.temp_dir.name) / "appdata")
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.temp_dir.cleanup()
            raise unittest.SkipTest(f"Tk is not available: {exc}") from exc
        self.root.withdraw()
        self.app = self.app_module.RubiMorphApp(self.root)

    def tearDown(self) -> None:
        for window in list(self.root.winfo_children()):
            if isinstance(window, tk.Toplevel):
                window.destroy()
        self.root.destroy()
        if self.old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self.old_appdata
        self.temp_dir.cleanup()

    def widget_texts(self, widget: tk.Misc) -> list[str]:
        texts: list[str] = []
        try:
            text = widget.cget("text")
        except tk.TclError:
            text = ""
        if isinstance(text, str) and text:
            texts.append(text)
        for child in widget.winfo_children():
            texts.extend(self.widget_texts(child))
        return texts

    def menu_labels(self) -> list[str]:
        labels: list[str] = []
        menu = self.root.nametowidget(self.root.cget("menu"))
        for index in range(menu.index("end") + 1):
            try:
                label = menu.entrycget(index, "label")
            except tk.TclError:
                label = ""
            if label:
                labels.append(label)
            try:
                submenu_name = menu.entrycget(index, "menu")
            except tk.TclError:
                submenu_name = ""
            if submenu_name:
                submenu = self.root.nametowidget(submenu_name)
                for sub_index in range(submenu.index("end") + 1):
                    try:
                        sub_label = submenu.entrycget(sub_index, "label")
                    except tk.TclError:
                        sub_label = ""
                    if sub_label:
                        labels.append(sub_label)
        return labels

    def test_main_layout_separates_text_and_file_workflows(self) -> None:
        self.assertEqual(
            [self.app.main_notebook.tab(i, "text") for i in range(self.app.main_notebook.index("end"))],
            ["テキスト変換", "ファイル変換"],
        )
        texts = self.widget_texts(self.root)
        self.assertIn("形式設定", texts)
        self.assertIn("処理単位", texts)
        self.assertNotIn("RubiMorph はローカルPC上で変換します。原稿本文を外部サーバーへ送信しません。", texts)
        button_texts = [
            widget.cget("text")
            for widget in self.root.winfo_children()
            for widget in widget.winfo_children()
            if isinstance(widget, ttk_button_classes())
        ]
        self.assertNotIn("カスタム形式", button_texts)
        self.assertNotIn("RubiMorphについて", button_texts)

    def test_menu_contains_custom_manager_and_web_links(self) -> None:
        labels = self.menu_labels()
        self.assertIn("カスタム形式を管理...", labels)
        self.assertIn("プロファイルをインポート...", labels)
        self.assertIn("操作マニュアルを開く", labels)
        self.assertIn("使用ガイドを開く", labels)
        self.assertIn("公式サイトを開く", labels)
        self.assertIn("最新版とRelease", labels)
        self.assertIn("OSSライセンス", labels)
        self.assertIn("RubiMorphについて", labels)

    def test_copy_result_copies_current_output(self) -> None:
        self.assertEqual(str(self.app.copy_button.cget("state")), "disabled")
        self.app._replace_output_text("converted result")
        self.assertEqual(str(self.app.copy_button.cget("state")), "normal")
        self.app.copy_result()
        self.assertEqual(self.root.clipboard_get(), "converted result")

    def test_plain_ruby_mode_is_available_only_for_plain_target(self) -> None:
        self.assertEqual(self.app.plain_mode_var.get(), "対象外")
        self.assertEqual(str(self.app.plain_combo.cget("state")), "disabled")

        self.app.target_var.set(self.app._label_for("plain", source=False))
        self.app._update_plain_mode_state()
        self.assertEqual(self.app.plain_mode_var.get(), "ルビを削除")
        self.assertEqual(str(self.app.plain_combo.cget("state")), "readonly")

        self.app.plain_mode_var.set("親文字（ルビ）で残す")
        self.app.target_var.set(self.app._label_for("html", source=False))
        self.app._update_plain_mode_state()
        self.assertEqual(self.app.plain_mode_var.get(), "対象外")
        self.assertEqual(str(self.app.plain_combo.cget("state")), "disabled")

        self.app.target_var.set(self.app._label_for("plain", source=False))
        self.app._update_plain_mode_state()
        self.assertEqual(self.app.plain_mode_var.get(), "親文字（ルビ）で残す")

    def test_log_and_warnings_are_available_from_details_button(self) -> None:
        diagnostic = SimpleNamespace(level="warning", code="sample", message="sample warning")
        self.app._append_log("sample log")
        self.app._append_diagnostics([diagnostic])
        self.assertEqual(self.app.warning_summary_var.get(), "警告 1件")
        self.assertEqual(str(self.app.details_button.cget("state")), "normal")
        self.app.show_conversion_details()
        titles = [child.title() for child in self.root.winfo_children() if isinstance(child, tk.Toplevel)]
        self.assertIn("ログと警告", titles)

    def test_result_status_summarizes_current_warnings_without_losing_details(self) -> None:
        diagnostic = SimpleNamespace(level="warning", code="sample", message="sample warning")
        self.app._append_diagnostics([diagnostic])
        self.app._set_result_status("変換が完了しました。")
        self.assertIn("警告が1件あります", self.app.status_var.get())
        self.assertIn("sample warning", self.app.status_var.get())
        self.assertEqual(self.app.warning_summary_var.get(), "警告 1件")

        self.app._clear_diagnostics()
        self.app._set_result_status("結果をクリップボードへコピーしました。")
        self.assertEqual(self.app.status_var.get(), "結果をクリップボードへコピーしました。")
        self.assertEqual(self.app.warning_summary_var.get(), "警告 0件")
        self.assertTrue(any("sample warning" in entry for entry in self.app.warning_entries))

    def test_web_link_constants_and_opening(self) -> None:
        self.assertEqual(self.app_module.MANUAL_URL, "https://www.tadatsune.com/RubiMorph/manual.html")
        self.assertEqual(self.app_module.GUIDE_URL, "https://www.tadatsune.com/RubiMorph/guide.html")
        self.assertEqual(self.app_module.OFFICIAL_SITE_URL, "https://www.tadatsune.com/")
        self.assertEqual(
            self.app_module.RELEASES_URL,
            "https://github.com/TadatsuneSakamoto/RubiMorph/releases/latest",
        )
        with mock.patch.object(self.app_module.webbrowser, "open_new_tab", return_value=True) as opener:
            self.app.open_web_page("操作マニュアル", self.app_module.MANUAL_URL)
        opener.assert_called_once_with(self.app_module.MANUAL_URL)

    def test_web_link_failure_is_handled_and_can_copy_url(self) -> None:
        with mock.patch.object(self.app_module.webbrowser, "open_new_tab", side_effect=RuntimeError("boom")):
            with mock.patch.object(self.app_module.messagebox, "askyesno", return_value=True):
                self.app.open_web_page("使用ガイド", self.app_module.GUIDE_URL)
        self.assertEqual(self.root.clipboard_get(), self.app_module.GUIDE_URL)

    def test_custom_profile_capabilities_control_format_lists(self) -> None:
        self.root.destroy()
        profiles_dir = Path(os.environ["APPDATA"]) / "RubiMorph" / "profiles"
        profiles_dir.mkdir(parents=True)
        input_only = self.app_module._default_profile_data()
        input_only["profile_id"] = "input-only"
        input_only["name"] = "Input Only"
        input_only["capabilities"] = {"input": True, "output": False}
        input_only.pop("renderer", None)
        output_only = self.app_module._default_profile_data()
        output_only["profile_id"] = "output-only"
        output_only["name"] = "Output Only"
        output_only["capabilities"] = {"input": False, "output": True}
        output_only.pop("parser", None)
        for data in (input_only, output_only):
            path = profiles_dir / f"{data['profile_id']}{self.app_module.PROFILE_EXTENSION}"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        self.root = tk.Tk()
        self.root.withdraw()
        self.app = self.app_module.RubiMorphApp(self.root)
        self.assertIn("カスタム: Input Only", self.app.source_labels)
        self.assertNotIn("カスタム: Input Only", self.app.target_labels)
        self.assertIn("カスタム: Output Only", self.app.target_labels)
        self.assertNotIn("カスタム: Output Only", self.app.source_labels)

    def test_custom_profile_reload_preserves_or_falls_back_safely(self) -> None:
        profiles_dir = Path(os.environ["APPDATA"]) / "RubiMorph" / "profiles"
        profiles_dir.mkdir(parents=True)
        data = self.app_module._default_profile_data()
        data["profile_id"] = "reload-test"
        data["name"] = "Reload Test"
        path = profiles_dir / f"reload-test{self.app_module.PROFILE_EXTENSION}"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.app.reload_custom_profiles(log=False)
        label = "カスタム: Reload Test"
        self.assertIn(label, self.app.source_labels)
        self.app.source_var.set(label)
        self.app.target_var.set(label)
        path.unlink()
        self.app.reload_custom_profiles(log=False)
        self.assertNotEqual(self.app.source_var.get(), label)
        self.assertNotEqual(self.app.target_var.get(), label)


def ttk_button_classes():
    import tkinter.ttk as ttk

    return (ttk.Button,)


if __name__ == "__main__":
    unittest.main()
