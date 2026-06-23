"""Tkinter desktop GUI for RubiMorph."""

from __future__ import annotations

import json
import re
import sys
import webbrowser
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from tkinter import Tk, filedialog, messagebox, scrolledtext, ttk
import tkinter as tk
import tkinter.font as tkfont
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = ROOT_DIR / "src" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from rubimorph import (  # noqa: E402
    APP_NAME,
    CustomFormatProfile,
    CustomParserRule,
    CustomTransformRule,
    EmphasisToken,
    ProfileCapabilities,
    ProfileError,
    PROFILE_EXTENSION,
    RenderOptions,
    RubyToken,
    TextToken,
    __version__,
    convert_text,
    convert_text_flexible,
    delete_registered_profile,
    export_registered_profile,
    import_profile_file,
    list_enabled_registered_profiles,
    load_registered_profiles,
    parse_custom_tokens,
    profile_from_data,
    register_profile,
    render_custom_tokens,
    save_profile,
    set_registered_profile_enabled,
    target_uses_plain_ruby_mode,
    validate_profile_data,
    validate_profile_file,
)
from rubimorph.fileops import TEXT_EXTENSIONS, convert_directory, convert_file  # noqa: E402
from rubimorph.platform_profiles import list_platform_profiles  # noqa: E402

BUILTIN_PLATFORM_OPTIONS = [
    (profile.platform_id, f"{profile.label} ({profile.platform_id})")
    for profile in list_platform_profiles()
    if profile.status in {"supported", "partial"}
]
PLAIN_MODE_LABELS = {
    "ルビを削除": "remove",
    "親文字（ルビ）で残す": "parentheses",
}
PLAIN_MODE_UNAVAILABLE_LABEL = "対象外"
APP_USER_MODEL_ID = f"TadatsuneSakamoto.RubiMorph.{__version__}"
ICON_RELATIVE_PATH = Path("assets") / "icons" / "rubimorph.ico"
MANUAL_URL = "https://www.tadatsune.com/RubiMorph/manual.html"
GUIDE_URL = "https://www.tadatsune.com/RubiMorph/guide.html"
OFFICIAL_SITE_URL = "https://www.tadatsune.com/"
RELEASES_URL = "https://github.com/TadatsuneSakamoto/RubiMorph/releases/latest"
ABOUT_LINKS = [
    ("X", "https://x.com/Tadatsune_S"),
    ("ホームページ", "https://www.tadatsune.com/"),
    ("GitHub", "https://github.com/TadatsuneSakamoto"),
    ("RubiMorph", "https://github.com/TadatsuneSakamoto/RubiMorph"),
]
LICENSE_DOCUMENTS = [
    ("OSS通知", Path("THIRD_PARTY_NOTICES.md")),
    ("Python 3.14.3", Path("LICENSES") / "Python-3.14.3-LICENSE.txt"),
    ("Tk 8.6", Path("LICENSES") / "Tk-8.6-license.terms"),
    ("PyInstaller 6.20.0", Path("LICENSES") / "PyInstaller-6.20.0-COPYING.txt"),
    ("Inno Setup 7", Path("LICENSES") / "Inno-Setup-7-license.txt"),
    ("RubiMorphライセンス", Path("LICENSE")),
]


class RubiMorphApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1120x760")
        self.root.minsize(920, 600)
        self._set_window_icon()
        self.selected_files: list[Path] = []
        self.single_input_file: Path | None = None
        self.single_output_file: Path | None = None
        self.input_folder: Path | None = None
        self.output_folder: Path | None = None
        self.multiple_output_folder: Path | None = None
        self.custom_profiles: list[CustomFormatProfile] = []
        self.custom_profile_by_id: dict[str, CustomFormatProfile] = {}
        self.source_choices: dict[str, tuple[str, str]] = {}
        self.target_choices: dict[str, tuple[str, str]] = {}
        self.source_labels: list[str] = []
        self.target_labels: list[str] = []
        self.log_entries: list[str] = []
        self.warning_entries: list[str] = []
        self.current_warning_entries: list[str] = []
        self.current_warning_messages: list[str] = []
        self.current_warning_count = 0
        self.last_plain_mode_label = "ルビを削除"
        self._load_custom_profiles()
        self._rebuild_format_choices()

        self.source_var = tk.StringVar(value=self._label_for("kakuyomu", source=True))
        self.target_var = tk.StringVar(value=self._label_for("html", source=False))
        self.plain_mode_var = tk.StringVar(value="ルビを削除")
        self.file_mode_var = tk.StringVar(value="single")
        self.file_label_var = tk.StringVar(value="入力ファイル未選択")
        self.single_input_var = tk.StringVar(value="")
        self.single_output_var = tk.StringVar(value="")
        self.multiple_summary_var = tk.StringVar(value="ファイル未選択")
        self.multiple_output_var = tk.StringVar(value="")
        self.input_folder_var = tk.StringVar(value="入力フォルダ未選択")
        self.output_folder_var = tk.StringVar(value="出力フォルダ未選択")
        self.status_var = tk.StringVar(value="準備完了")
        self.warning_summary_var = tk.StringVar(value="警告 0件")

        self._build_widgets()

    def _build_widgets(self) -> None:
        self._build_menu()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self._build_format_settings()
        self._build_work_area()
        self._build_status_bar()
        self._update_plain_mode_state()

    def _build_format_settings(self) -> None:
        controls = ttk.LabelFrame(self.root, text="形式設定", padding=(10, 8))
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        controls.columnconfigure(1, weight=1, uniform="format")
        controls.columnconfigure(4, weight=1, uniform="format")
        controls.columnconfigure(6, weight=1, uniform="format")

        ttk.Label(controls, text="変換元").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.source_combo = ttk.Combobox(
            controls,
            textvariable=self.source_var,
            values=self.source_labels,
            state="readonly",
            width=24,
        )
        self.source_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(controls, text="→").grid(row=0, column=2, sticky="ew", padx=(0, 10))
        ttk.Label(controls, text="変換先").grid(row=0, column=3, sticky="w", padx=(0, 6))
        self.target_combo = ttk.Combobox(
            controls,
            textvariable=self.target_var,
            values=self.target_labels,
            state="readonly",
            width=24,
        )
        self.target_combo.grid(row=0, column=4, sticky="ew", padx=(0, 14))
        self.target_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_plain_mode_state())

        ttk.Label(controls, text="ルビ出力").grid(row=0, column=5, sticky="w", padx=(0, 6))
        self.plain_combo = ttk.Combobox(
            controls,
            textvariable=self.plain_mode_var,
            values=list(PLAIN_MODE_LABELS.keys()),
            state="readonly",
            width=20,
        )
        self.plain_combo.grid(row=0, column=6, sticky="ew")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        custom_menu = tk.Menu(menubar, tearoff=False)
        custom_menu.add_command(label="カスタム形式を管理...", command=self.show_custom_profiles)
        custom_menu.add_command(label="プロファイルをインポート...", command=self.import_custom_profile)
        custom_menu.add_separator()
        custom_menu.add_command(label="形式一覧を再読み込み", command=self.reload_custom_profiles)
        menubar.add_cascade(label="カスタム形式", menu=custom_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(
            label="操作マニュアルを開く",
            command=lambda: self.open_web_page("操作マニュアル", MANUAL_URL),
        )
        help_menu.add_command(
            label="使用ガイドを開く",
            command=lambda: self.open_web_page("使用ガイド", GUIDE_URL),
        )
        help_menu.add_command(
            label="公式サイトを開く",
            command=lambda: self.open_web_page("公式サイト", OFFICIAL_SITE_URL),
        )
        help_menu.add_command(
            label="最新版とRelease",
            command=lambda: self.open_web_page("最新版とRelease", RELEASES_URL),
        )
        help_menu.add_separator()
        help_menu.add_command(label="OSSライセンス", command=self.show_oss_licenses)
        help_menu.add_command(label="RubiMorphについて", command=self.show_about)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        self.root.configure(menu=menubar)

    def _build_work_area(self) -> None:
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        text_tab = ttk.Frame(self.main_notebook, padding=10)
        file_tab = ttk.Frame(self.main_notebook, padding=10)
        self.main_notebook.add(text_tab, text="テキスト変換")
        self.main_notebook.add(file_tab, text="ファイル変換")

        self._build_text_tab(text_tab)
        self._build_file_tab(file_tab)

    def _build_text_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        panes = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        panes.grid(row=0, column=0, sticky="nsew")

        input_frame = ttk.LabelFrame(panes, text="入力テキスト", padding=(8, 6))
        output_frame = ttk.LabelFrame(panes, text="変換結果", padding=(8, 6))
        input_frame.rowconfigure(1, weight=1)
        input_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        output_frame.columnconfigure(0, weight=1)
        panes.add(input_frame, weight=1)
        panes.add(output_frame, weight=1)

        ttk.Label(input_frame, text="貼り付けまたは入力").grid(row=0, column=0, sticky="w")
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, undo=True)
        self.input_text.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        output_header = ttk.Frame(output_frame)
        output_header.grid(row=0, column=0, sticky="ew")
        output_header.columnconfigure(0, weight=1)
        ttk.Label(output_header, text="選択・コピーできます").grid(row=0, column=0, sticky="w")
        self.copy_button = ttk.Button(
            output_header,
            text="コピー",
            command=self.copy_result,
            state=tk.DISABLED,
        )
        self.copy_button.grid(row=0, column=1, sticky="e")
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, undo=True)
        self.output_text.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        actions = ttk.Frame(parent)
        actions.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        actions.columnconfigure(0, weight=1)
        self.text_convert_button = ttk.Button(
            actions,
            text="変換",
            command=self.convert_direct_text,
            width=18,
        )
        self.text_convert_button.grid(row=0, column=1, sticky="e")

    def _build_file_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        mode_frame = ttk.LabelFrame(parent, text="処理単位", padding=(8, 6))
        mode_frame.grid(row=0, column=0, sticky="ew")
        for column in range(3):
            mode_frame.columnconfigure(column, weight=1)
        for column, (label, value) in enumerate(
            (("単一ファイル", "single"), ("複数ファイル", "multiple"), ("フォルダ一括", "folder"))
        ):
            ttk.Radiobutton(
                mode_frame,
                text=label,
                value=value,
                variable=self.file_mode_var,
                command=self._update_file_mode_visibility,
            ).grid(row=0, column=column, sticky="w", padx=(0, 16))

        self.file_mode_container = ttk.Frame(parent)
        self.file_mode_container.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.file_mode_container.rowconfigure(0, weight=1)
        self.file_mode_container.columnconfigure(0, weight=1)

        self.single_file_frame = self._build_single_file_frame(self.file_mode_container)
        self.multiple_file_frame = self._build_multiple_file_frame(self.file_mode_container)
        self.folder_file_frame = self._build_folder_file_frame(self.file_mode_container)
        self.file_mode_frames = {
            "single": self.single_file_frame,
            "multiple": self.multiple_file_frame,
            "folder": self.folder_file_frame,
        }
        for frame in self.file_mode_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        self._update_file_mode_visibility()

    def _build_single_file_frame(self, parent: ttk.Frame) -> ttk.Frame:
        frame = ttk.LabelFrame(parent, text="単一ファイル", padding=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="入力ファイル").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(frame, textvariable=self.single_input_var, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=(0, 8), pady=(0, 8)
        )
        ttk.Button(frame, text="参照...", command=self.choose_single_input_file).grid(
            row=0, column=2, sticky="ew", pady=(0, 8)
        )
        ttk.Label(frame, text="出力先").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(frame, textvariable=self.single_output_var, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=(0, 8), pady=(0, 8)
        )
        ttk.Button(frame, text="参照...", command=self.choose_single_output_file).grid(
            row=1, column=2, sticky="ew", pady=(0, 8)
        )
        self.single_convert_button = ttk.Button(
            frame,
            text="変換開始",
            command=self.convert_single_file,
            state=tk.DISABLED,
        )
        self.single_convert_button.grid(row=2, column=2, sticky="ew", pady=(8, 0))
        return frame

    def _build_multiple_file_frame(self, parent: ttk.Frame) -> ttk.Frame:
        frame = ttk.LabelFrame(parent, text="複数ファイル", padding=10)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="選択ファイル").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(frame, textvariable=self.multiple_summary_var, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=(0, 8), pady=(0, 8)
        )
        ttk.Button(frame, text="ファイルを選択...", command=self.choose_multiple_files).grid(
            row=0, column=2, sticky="ew", pady=(0, 8)
        )

        list_frame = ttk.Frame(frame)
        list_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 8), pady=(0, 8))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.multiple_files_list = tk.Listbox(list_frame, height=7, activestyle="dotbox")
        self.multiple_files_list.grid(row=0, column=0, sticky="nsew")
        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.multiple_files_list.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.multiple_files_list.configure(yscrollcommand=list_scroll.set)

        ttk.Label(frame, text="出力フォルダ").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(frame, textvariable=self.multiple_output_var, state="readonly").grid(
            row=2, column=1, sticky="ew", padx=(0, 8), pady=(0, 8)
        )
        ttk.Button(frame, text="参照...", command=self.choose_multiple_output_folder).grid(
            row=2, column=2, sticky="ew", pady=(0, 8)
        )
        self.multiple_convert_button = ttk.Button(
            frame,
            text="変換開始",
            command=self.convert_multiple_files,
            state=tk.DISABLED,
        )
        self.multiple_convert_button.grid(row=3, column=2, sticky="ew", pady=(8, 0))
        return frame

    def _build_folder_file_frame(self, parent: ttk.Frame) -> ttk.Frame:
        frame = ttk.LabelFrame(parent, text="フォルダ一括", padding=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="入力フォルダ").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(frame, textvariable=self.input_folder_var, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=(0, 8), pady=(0, 8)
        )
        ttk.Button(frame, text="参照...", command=self.choose_input_folder).grid(
            row=0, column=2, sticky="ew", pady=(0, 8)
        )
        ttk.Label(frame, text="出力フォルダ").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(frame, textvariable=self.output_folder_var, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=(0, 8), pady=(0, 8)
        )
        ttk.Button(frame, text="参照...", command=self.choose_output_folder).grid(
            row=1, column=2, sticky="ew", pady=(0, 8)
        )
        self.folder_convert_button = ttk.Button(
            frame,
            text="変換開始",
            command=self.convert_folder,
            state=tk.DISABLED,
        )
        self.folder_convert_button.grid(row=2, column=2, sticky="ew", pady=(8, 0))
        return frame

    def _build_status_bar(self) -> None:
        status = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        status.grid(row=2, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        ttk.Separator(status, orient=tk.HORIZONTAL).grid(
            row=0, column=0, columnspan=3, sticky="ew", pady=(0, 6)
        )
        ttk.Label(status, textvariable=self.status_var).grid(row=1, column=0, sticky="w")
        ttk.Label(status, textvariable=self.warning_summary_var).grid(row=1, column=1, sticky="e", padx=(10, 8))
        self.details_button = ttk.Button(
            status,
            text="詳細...",
            command=self.show_conversion_details,
            state=tk.DISABLED,
        )
        self.details_button.grid(row=1, column=2, sticky="e")

    def _update_file_mode_visibility(self) -> None:
        selected = self.file_mode_var.get()
        for mode, frame in self.file_mode_frames.items():
            if mode == selected:
                frame.grid()
            else:
                frame.grid_remove()
        self._update_file_action_state()

    def _update_file_action_state(self) -> None:
        if hasattr(self, "single_convert_button"):
            state = tk.NORMAL if self.single_input_file and self.single_output_file else tk.DISABLED
            self.single_convert_button.configure(state=state)
        if hasattr(self, "multiple_convert_button"):
            state = tk.NORMAL if self.selected_files and self.multiple_output_folder else tk.DISABLED
            self.multiple_convert_button.configure(state=state)
        if hasattr(self, "folder_convert_button"):
            state = tk.NORMAL if self.input_folder and self.output_folder else tk.DISABLED
            self.folder_convert_button.configure(state=state)

    def convert_direct_text(self) -> None:
        source_text = self.input_text.get("1.0", "end-1c")
        source_platform, source_profile = self._source_selection()
        target_platform, target_profile = self._target_selection()
        try:
            result = convert_text_flexible(
                source_text,
                source_platform=source_platform,
                target_platform=target_platform,
                source_profile=source_profile,
                target_profile=target_profile,
                options=self._options_for_target(),
            )
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"テキスト変換エラー: {exc}")
            self._record_failure("テキスト変換できませんでした。詳細を確認してください。")
            messagebox.showerror("テキスト変換エラー", str(exc), parent=self.root)
            return
        self._replace_output_text(result.output)
        self._show_diagnostics(result.diagnostics)
        warning_count = self._warning_count(result.diagnostics)
        self._append_log(f"テキストを変換しました。警告: {warning_count}件")
        self._set_result_status("変換が完了しました。")

    def copy_result(self) -> None:
        text = self.output_text.get("1.0", tk.END).rstrip("\n")
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._append_log("変換結果をクリップボードへコピーしました。")
        self._clear_diagnostics()
        self._set_result_status("結果をクリップボードへコピーしました。")

    def choose_single_input_file(self) -> None:
        path = filedialog.askopenfilename(
            title="入力ファイルを選択",
            filetypes=[("Text files", "*.txt *.md"), ("All files", "*.*")],
        )
        if not path:
            return
        file_path = Path(path)
        self.single_input_file = file_path
        self.single_input_var.set(str(file_path))
        self.file_label_var.set(f"入力ファイル: {file_path}")
        if self.single_output_file is None:
            default_output = file_path.with_name(f"{file_path.stem}_converted{file_path.suffix}")
            self.single_output_file = default_output
            self.single_output_var.set(str(default_output))
        self._append_log(f"入力ファイルを選択しました: {file_path}")
        self._set_status("単一ファイルを選択しました")
        self._update_file_action_state()

    def choose_single_output_file(self) -> None:
        initial = self.single_output_file
        if initial is None and self.single_input_file is not None:
            initial = self.single_input_file.with_name(
                f"{self.single_input_file.stem}_converted{self.single_input_file.suffix}"
            )
        path = filedialog.asksaveasfilename(
            title="出力先を選択",
            defaultextension=".txt",
            initialdir=str(initial.parent) if initial else None,
            initialfile=initial.name if initial else None,
            filetypes=[("Text files", "*.txt"), ("Markdown", "*.md"), ("All files", "*.*")],
        )
        if not path:
            return
        self.single_output_file = Path(path)
        self.single_output_var.set(str(self.single_output_file))
        self._append_log(f"単一ファイルの出力先を選択しました: {self.single_output_file}")
        self._set_status("出力先を選択しました")
        self._update_file_action_state()

    def choose_input_file(self) -> None:
        self.file_mode_var.set("single")
        self._update_file_mode_visibility()
        self.choose_single_input_file()

    def choose_multiple_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="複数ファイルを選択",
            filetypes=[("Text files", "*.txt *.md"), ("All files", "*.*")],
        )
        if not paths:
            return
        self.selected_files = [Path(path) for path in paths]
        self.multiple_summary_var.set(f"{len(self.selected_files)}件を選択")
        self.multiple_files_list.delete(0, tk.END)
        for file_path in self.selected_files:
            self.multiple_files_list.insert(tk.END, str(file_path))
        self._append_log(f"複数ファイルを選択しました: {len(self.selected_files)}件")
        self._set_status("複数ファイルを選択しました")
        self._update_file_action_state()

    def choose_multiple_output_folder(self) -> None:
        path = filedialog.askdirectory(title="出力フォルダを選択")
        if not path:
            return
        self.multiple_output_folder = Path(path)
        self.multiple_output_var.set(str(self.multiple_output_folder))
        self._append_log(f"複数ファイルの出力フォルダを選択しました: {self.multiple_output_folder}")
        self._set_status("出力フォルダを選択しました")
        self._update_file_action_state()

    def choose_input_folder(self) -> None:
        path = filedialog.askdirectory(title="入力フォルダを選択")
        if not path:
            return
        self.input_folder = Path(path)
        self.input_folder_var.set(str(self.input_folder))
        self._append_log(f"入力フォルダを選択しました: {self.input_folder}")
        self._set_status("入力フォルダを選択しました")
        self._update_file_action_state()

    def choose_output_folder(self) -> None:
        path = filedialog.askdirectory(title="出力フォルダを選択")
        if not path:
            return
        self.output_folder = Path(path)
        self.output_folder_var.set(str(self.output_folder))
        self._append_log(f"出力フォルダを選択しました: {self.output_folder}")
        self._set_status("出力フォルダを選択しました")
        self._update_file_action_state()

    def batch_convert(self) -> None:
        mode = self.file_mode_var.get()
        if mode == "single":
            self.convert_single_file()
        elif mode == "multiple":
            self.convert_multiple_files()
        else:
            self.convert_folder()

    def convert_single_file(self) -> None:
        if self.single_input_file is None or self.single_output_file is None:
            messagebox.showwarning("入力または出力先未選択", "入力ファイルと出力先を選択してください。", parent=self.root)
            return
        source_platform, source_profile = self._source_selection()
        target_platform, target_profile = self._target_selection()
        try:
            result = convert_file(
                self.single_input_file,
                self.single_output_file,
                source_platform,
                target_platform,
                self._options_for_target(),
                source_profile=source_profile,
                target_profile=target_profile,
            )
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"単一ファイル変換エラー: {self.single_input_file} / {exc}")
            self._record_failure("単一ファイルを変換できませんでした。詳細を確認してください。")
            messagebox.showerror("単一ファイル変換エラー", str(exc), parent=self.root)
            return
        self._show_diagnostics(result.diagnostics)
        self._append_file_result(result)
        self._set_result_status("1ファイルを変換しました。")

    def convert_multiple_files(self) -> None:
        if not self.selected_files or self.multiple_output_folder is None:
            messagebox.showwarning("入力または出力先未選択", "選択ファイルと出力フォルダを指定してください。", parent=self.root)
            return

        pairs = [
            (source, self.multiple_output_folder / source.name)
            for source in self.selected_files
            if source.suffix.lower() in TEXT_EXTENSIONS
        ]
        if not pairs:
            messagebox.showwarning("対象ファイルなし", "変換対象の .txt または .md ファイルがありません。", parent=self.root)
            return

        results = []
        failures = 0
        self._clear_diagnostics()
        source_platform, source_profile = self._source_selection()
        target_platform, target_profile = self._target_selection()
        for source, destination in pairs:
            try:
                result = convert_file(
                    source,
                    destination,
                    source_platform,
                    target_platform,
                    self._options_for_target(),
                    source_profile=source_profile,
                    target_profile=target_profile,
                )
                results.append(result)
                self._append_file_result(result)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                self._append_log(f"ERROR: {source} / {exc}")
        self._append_batch_summary(results, failures)
        if failures == 0:
            self._set_result_status(f"{len(results)}ファイルを変換しました。")
        else:
            self._set_result_status(
                f"{len(results)}ファイルを変換しました。{failures}ファイルは変換できませんでした。"
            )

    def convert_folder(self) -> None:
        if self.input_folder is None or self.output_folder is None:
            messagebox.showwarning("入力または出力先未選択", "入力フォルダと出力フォルダを選択してください。", parent=self.root)
            return
        try:
            source_platform, source_profile = self._source_selection()
            target_platform, target_profile = self._target_selection()
            results = convert_directory(
                self.input_folder,
                self.output_folder,
                source_platform,
                target_platform,
                self._options_for_target(),
                source_profile=source_profile,
                target_profile=target_profile,
            )
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"フォルダ一括変換エラー: {exc}")
            self._record_failure("フォルダ一括変換できませんでした。詳細を確認してください。")
            messagebox.showerror("フォルダ一括変換エラー", str(exc), parent=self.root)
            return

        self._clear_diagnostics()
        for result in results:
            self._append_file_result(result)
        self._append_batch_summary(results, failures=0)
        self._set_result_status(f"フォルダ変換が完了しました。{len(results)}ファイルを変換しました。")

    def show_about(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{APP_NAME}について")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.columnconfigure(1, weight=1)

        ttk.Label(dialog, text=f"{APP_NAME} {__version__}", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8)
        )
        ttk.Label(dialog, text="開発者: Tadatsune Sakamoto").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 8)
        )

        for row, (label, url) in enumerate(ABOUT_LINKS, start=2):
            ttk.Label(dialog, text=f"{label}:").grid(
                row=row, column=0, sticky="nw", padx=(16, 8), pady=2
            )
            self._link_label(dialog, url).grid(row=row, column=1, sticky="w", padx=(0, 16), pady=2)

        ttk.Button(dialog, text="閉じる", command=dialog.destroy).grid(
            row=6, column=0, columnspan=2, sticky="e", padx=16, pady=(12, 16)
        )
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.grab_set()

    def show_oss_licenses(self) -> None:
        documents: list[tuple[str, str]] = []
        missing: list[Path] = []
        for title, relative_path in LICENSE_DOCUMENTS:
            path = _resource_path(relative_path)
            if not path.is_file():
                missing.append(relative_path)
                continue
            try:
                documents.append((title, path.read_text(encoding="utf-8")))
            except OSError as exc:
                messagebox.showerror("OSSライセンス読み込みエラー", f"{path}\n{exc}")
                return

        if missing:
            messagebox.showerror(
                "OSSライセンス読み込みエラー",
                "配布物に必要なライセンス・通知ファイルが見つかりません。\n\n"
                + "\n".join(str(path) for path in missing),
            )
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("OSSライセンス")
        dialog.transient(self.root)
        dialog.geometry("900x640")
        dialog.minsize(640, 420)
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(dialog)
        notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        for title, text in documents:
            frame = ttk.Frame(notebook)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            viewer = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
            viewer.insert("1.0", text)
            viewer.grid(row=0, column=0, sticky="nsew")
            self._make_read_only_text(viewer)
            notebook.add(frame, text=title)

        ttk.Button(dialog, text="閉じる", command=dialog.destroy).grid(
            row=1, column=0, sticky="e", padx=10, pady=(0, 10)
        )
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.grab_set()

    def _link_label(self, parent: tk.Misc, url: str) -> ttk.Label:
        font = tkfont.nametofont("TkDefaultFont").copy()
        font.configure(underline=True)
        label = ttk.Label(parent, text=url, foreground="#0366d6", cursor="hand2", font=font)
        label.configure(takefocus=True)
        label.bind("<Button-1>", lambda _event: self._open_link(url))
        label.bind("<Return>", lambda _event: self._open_link(url))
        label.bind("<space>", lambda _event: self._open_link(url))
        return label

    def _open_link(self, url: str) -> str:
        self.open_web_page("リンク", url)
        return "break"

    def open_web_page(self, page_name: str, url: str) -> None:
        try:
            opened = webbrowser.open_new_tab(url)
        except Exception as exc:  # noqa: BLE001
            self._show_web_open_error(page_name, url, exc)
            return
        if opened is False:
            self._show_web_open_error(page_name, url, None)

    def _show_web_open_error(self, page_name: str, url: str, exc: Exception | None) -> None:
        reason = f"\n\n{exc}" if exc else ""
        should_copy = messagebox.askyesno(
            "リンクを開けません",
            f"{page_name}をブラウザで開けませんでした。\n\n{url}{reason}\n\nURLをクリップボードへコピーしますか。",
            parent=self.root,
        )
        if should_copy:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self._set_status(f"{page_name}のURLをコピーしました")

    def _make_read_only_text(self, widget: tk.Text) -> None:
        def handle_key(event) -> str | None:
            ctrl = bool(event.state & 0x4)
            key = event.keysym.lower()
            if ctrl and key == "c":
                return None
            if ctrl and key == "a":
                widget.tag_add(tk.SEL, "1.0", "end-1c")
                widget.mark_set(tk.INSERT, "1.0")
                widget.see(tk.INSERT)
                return "break"
            if event.keysym in {
                "Left",
                "Right",
                "Up",
                "Down",
                "Home",
                "End",
                "Prior",
                "Next",
                "Tab",
                "ISO_Left_Tab",
            }:
                return None
            return "break"

        widget.bind("<Key>", handle_key)
        widget.bind("<<Cut>>", lambda _event: "break")
        widget.bind("<<Paste>>", lambda _event: "break")
        widget.bind("<<Clear>>", lambda _event: "break")
        widget.bind("<Button-2>", lambda _event: "break")

    def _append_file_result(self, result) -> None:
        warning_count = self._warning_count(result.diagnostics)
        self._append_log(f"OK: {result.source} -> {result.destination} / 警告 {warning_count}件")
        self._append_diagnostics(result.diagnostics, str(result.source))

    def _append_batch_summary(self, results, failures: int) -> None:
        total_warnings = sum(self._warning_count(result.diagnostics) for result in results)
        self._append_log(
            f"ファイル変換完了: 成功 {len(results)}件 / エラー {failures}件 / 警告 {total_warnings}件"
        )

    def show_custom_profiles(self) -> "CustomProfileManagerDialog":
        return CustomProfileManagerDialog(self)

    def import_custom_profile(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="カスタム形式プロファイルをインポート",
            filetypes=[("RubiMorph profile", f"*{PROFILE_EXTENSION}"), ("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            import_profile_file(path)
        except ProfileError as exc:
            if "既に登録" not in str(exc):
                messagebox.showerror("インポートエラー", str(exc), parent=self.root)
                return
            if not messagebox.askyesno("上書き確認", f"{exc}\n上書きしますか。", parent=self.root):
                return
            try:
                import_profile_file(path, overwrite=True)
            except ProfileError as retry_exc:
                messagebox.showerror("インポートエラー", str(retry_exc), parent=self.root)
                return
        self.reload_custom_profiles(log=False)
        self._append_log(f"カスタム形式をインポートしました: {path}")
        self._clear_diagnostics()
        self._set_result_status("カスタム形式をインポートしました。")

    def reload_custom_profiles(self, *, log: bool = True) -> None:
        previous_source = self.source_var.get()
        previous_target = self.target_var.get()
        self._load_custom_profiles()
        self._rebuild_format_choices()
        if hasattr(self, "source_combo"):
            self.source_combo.configure(values=self.source_labels)
            self.target_combo.configure(values=self.target_labels)
        self.source_var.set(
            previous_source if previous_source in self.source_choices else self._label_for("kakuyomu", source=True)
        )
        self.target_var.set(
            previous_target if previous_target in self.target_choices else self._label_for("html", source=False)
        )
        self._update_plain_mode_state()
        if log:
            self._append_log("カスタム形式を再読み込みしました。")
            self._clear_diagnostics()
            self._set_result_status("カスタム形式を再読み込みしました。")

    def _load_custom_profiles(self) -> None:
        self.custom_profiles = list_enabled_registered_profiles()
        self.custom_profile_by_id = {profile.profile_id: profile for profile in self.custom_profiles}

    def _rebuild_format_choices(self) -> None:
        self.source_choices = {}
        self.target_choices = {}
        self.source_labels = []
        self.target_labels = []
        for platform_id, label in BUILTIN_PLATFORM_OPTIONS:
            self.source_choices[label] = ("platform", platform_id)
            self.target_choices[label] = ("platform", platform_id)
            self.source_labels.append(label)
            self.target_labels.append(label)
        for profile in self.custom_profiles:
            label = self._custom_label(profile)
            if profile.capabilities.input:
                self.source_choices[label] = ("custom", profile.profile_id)
                self.source_labels.append(label)
            if profile.capabilities.output:
                self.target_choices[label] = ("custom", profile.profile_id)
                self.target_labels.append(label)

    def _source_selection(self) -> tuple[str | None, CustomFormatProfile | None]:
        return self._selection_from_label(self.source_var.get(), self.source_choices)

    def _target_selection(self) -> tuple[str | None, CustomFormatProfile | None]:
        return self._selection_from_label(self.target_var.get(), self.target_choices)

    def _selected_target_uses_plain_ruby_mode(self) -> bool:
        target_platform, target_profile = self._target_selection()
        return target_uses_plain_ruby_mode(target_platform, target_profile)

    def _selection_from_label(
        self,
        label: str,
        choices: dict[str, tuple[str, str]],
    ) -> tuple[str | None, CustomFormatProfile | None]:
        if label not in choices:
            label = next(iter(choices))
        kind, value = choices[label]
        if kind == "custom":
            return None, self.custom_profile_by_id[value]
        return value, None

    def _options(self) -> RenderOptions:
        label = self.plain_mode_var.get()
        if label not in PLAIN_MODE_LABELS:
            label = self.last_plain_mode_label
        return RenderOptions(plain_ruby_mode=PLAIN_MODE_LABELS[label])

    def _options_for_target(self) -> RenderOptions | None:
        if not self._selected_target_uses_plain_ruby_mode():
            return None
        return self._options()

    def _update_plain_mode_state(self) -> None:
        if not hasattr(self, "plain_combo"):
            return
        if self._selected_target_uses_plain_ruby_mode():
            if self.plain_mode_var.get() == PLAIN_MODE_UNAVAILABLE_LABEL:
                self.plain_mode_var.set(self.last_plain_mode_label)
            self.plain_combo.configure(values=list(PLAIN_MODE_LABELS.keys()), state="readonly")
            return

        current = self.plain_mode_var.get()
        if current in PLAIN_MODE_LABELS:
            self.last_plain_mode_label = current
        self.plain_combo.configure(values=[PLAIN_MODE_UNAVAILABLE_LABEL], state=tk.DISABLED)
        self.plain_mode_var.set(PLAIN_MODE_UNAVAILABLE_LABEL)

    def _show_diagnostics(self, diagnostics) -> None:
        self._clear_diagnostics()
        self._append_diagnostics(diagnostics)

    def _clear_diagnostics(self) -> None:
        self.current_warning_entries = []
        self.current_warning_messages = []
        self.current_warning_count = 0
        self._update_warning_summary()

    def _append_diagnostics(self, diagnostics, prefix: str | None = None) -> None:
        for diagnostic in diagnostics:
            head = f"{prefix}: " if prefix else ""
            entry = f"[{diagnostic.level.upper()}] {head}{diagnostic.code}: {diagnostic.message}"
            self.warning_entries.append(entry)
            self.current_warning_entries.append(entry)
            if diagnostic.level == "warning":
                self.current_warning_messages.append(str(diagnostic.message))
        self.current_warning_count = self._warning_count_from_entries()
        self._update_warning_summary()

    def _append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_entries.append(f"[{timestamp}] {message}")
        self._update_details_button()

    def _warning_count_from_entries(self) -> int:
        return sum(1 for entry in self.current_warning_entries if entry.startswith("[WARNING]"))

    def _update_warning_summary(self) -> None:
        self.warning_summary_var.set(f"警告 {self.current_warning_count}件")
        self._update_details_button()

    def _update_details_button(self) -> None:
        if hasattr(self, "details_button"):
            state = tk.NORMAL if self.log_entries or self.warning_entries else tk.DISABLED
            self.details_button.configure(state=state)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _set_result_status(self, message: str) -> None:
        if self.current_warning_count <= 0:
            self.status_var.set(message)
            return

        warning_text = f"{message} 警告が{self.current_warning_count}件あります。"
        summary = self._current_warning_excerpt()
        if summary:
            warning_text = f"{warning_text} {summary}"
        self.status_var.set(warning_text)

    def _record_failure(self, message: str) -> None:
        self._clear_diagnostics()
        self.status_var.set(message)

    def _current_warning_excerpt(self) -> str:
        if not self.current_warning_messages:
            return ""
        summary = re.sub(r"\s+", " ", self.current_warning_messages[0]).strip()
        if len(summary) > 70:
            return f"{summary[:69]}…"
        return summary

    def _replace_output_text(self, text: str) -> None:
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.copy_button.configure(state=tk.NORMAL if text else tk.DISABLED)

    def show_conversion_details(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("ログと警告")
        dialog.transient(self.root)
        dialog.geometry("860x520")
        dialog.minsize(640, 360)
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(dialog)
        notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self._add_detail_tab(notebook, "ログ", "\n".join(self.log_entries) or "ログはありません。")
        self._add_detail_tab(notebook, "警告", "\n".join(self.warning_entries) or "警告はありません。")

        ttk.Button(dialog, text="閉じる", command=dialog.destroy).grid(
            row=1, column=0, sticky="e", padx=10, pady=(0, 10)
        )
        dialog.bind("<Escape>", lambda _event: dialog.destroy())

    def _add_detail_tab(self, notebook: ttk.Notebook, title: str, text: str) -> None:
        frame = ttk.Frame(notebook)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        viewer = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        viewer.grid(row=0, column=0, sticky="nsew")
        viewer.insert("1.0", text)
        self._make_read_only_text(viewer)
        notebook.add(frame, text=title)

    def _label_for(self, platform_id: str, *, source: bool) -> str:
        labels = self.source_labels if source else self.target_labels
        for key, label in BUILTIN_PLATFORM_OPTIONS:
            if key == platform_id:
                return label
        return labels[0]

    @staticmethod
    def _custom_label(profile: CustomFormatProfile) -> str:
        return f"カスタム: {profile.name}"

    def _set_window_icon(self) -> None:
        icon_path = _resource_path(ICON_RELATIVE_PATH)
        if icon_path.is_file():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass

    @staticmethod
    def _warning_count(diagnostics) -> int:
        return sum(1 for diagnostic in diagnostics if diagnostic.level == "warning")


class CustomProfileManagerDialog:
    def __init__(self, app: RubiMorphApp) -> None:
        self.app = app
        self.dialog = tk.Toplevel(app.root)
        self.dialog.title("カスタム形式プロファイル")
        self.dialog.transient(app.root)
        self.dialog.geometry("1100x560")
        self.dialog.minsize(860, 420)
        self.dialog.rowconfigure(0, weight=1)
        self.dialog.columnconfigure(0, weight=1)
        self.records = []
        self.records_by_iid: dict[str, Any] = {}
        self._build()
        self.refresh()
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
        self.dialog.grab_set()

    def _build(self) -> None:
        frame = ttk.Frame(self.dialog, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        columns = ("name", "id", "input", "output", "enabled", "validation", "path", "modified")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "name": "プロファイル名",
            "id": "プロファイルID",
            "input": "入力対応",
            "output": "出力対応",
            "enabled": "有効状態",
            "validation": "検証状態",
            "path": "保存場所",
            "modified": "最終更新日時",
        }
        widths = {
            "name": 160,
            "id": 140,
            "input": 70,
            "output": 70,
            "enabled": 80,
            "validation": 120,
            "path": 280,
            "modified": 140,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        buttons = ttk.Frame(frame)
        buttons.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        actions = [
            ("新規作成", self.new_profile),
            ("編集", self.edit_profile),
            ("複製", self.duplicate_profile),
            ("検証", self.validate_selected),
            ("登録", self.enable_selected),
            ("登録解除", self.disable_selected),
            ("インポート", self.import_profile),
            ("エクスポート", self.export_profile),
            ("削除", self.delete_selected),
            ("保存", self.save_selected),
            ("名前を付けて保存", self.save_selected_as),
            ("閉じる", self.close),
        ]
        for index, (label, command) in enumerate(actions):
            ttk.Button(buttons, text=label, command=command).grid(
                row=index // 6,
                column=index % 6,
                sticky="ew",
                padx=(0, 6),
                pady=(0, 6),
            )
            buttons.columnconfigure(index % 6, weight=1)

    def refresh(self) -> None:
        self.records = load_registered_profiles()
        self.records_by_iid.clear()
        self.tree.delete(*self.tree.get_children())
        for index, record in enumerate(self.records):
            iid = str(index)
            profile = record.profile
            validation = (
                "OK"
                if record.validation.is_valid
                else f"エラー {len(record.validation.errors)}件"
            )
            modified = (
                datetime.fromtimestamp(record.modified_at).strftime("%Y-%m-%d %H:%M")
                if record.modified_at
                else ""
            )
            values = (
                profile.name if profile else "",
                profile.profile_id if profile else "",
                "はい" if profile and profile.capabilities.input else "いいえ",
                "はい" if profile and profile.capabilities.output else "いいえ",
                "有効" if record.enabled else "無効",
                validation,
                str(record.path),
                modified,
            )
            self.tree.insert("", tk.END, iid=iid, values=values)
            self.records_by_iid[iid] = record

    def close(self) -> None:
        self.app.reload_custom_profiles(log=False)
        self.dialog.destroy()

    def _refresh_after_change(self) -> None:
        self.refresh()
        self.app.reload_custom_profiles(log=False)

    def _selected_record(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("未選択", "プロファイルを選択してください。", parent=self.dialog)
            return None
        return self.records_by_iid[selection[0]]

    def new_profile(self) -> None:
        editor = ProfileEditorDialog(self.dialog, _default_profile_data(), "カスタム形式を新規作成")
        profile = editor.show()
        if profile is None:
            return
        try:
            register_profile(profile)
        except ProfileError as exc:
            self.app._append_log(f"カスタム形式の登録エラー: {exc}")
            self.app._record_failure("カスタム形式を登録できませんでした。詳細を確認してください。")
            messagebox.showerror("保存エラー", str(exc), parent=self.dialog)
            return
        self._refresh_after_change()
        self.app._append_log(f"カスタム形式を登録しました: {profile.profile_id}")
        self.app._clear_diagnostics()
        self.app._set_result_status("カスタム形式を登録しました。")

    def edit_profile(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        if record.profile is None:
            self.validate_selected()
            return
        original_id = record.profile.profile_id
        editor = ProfileEditorDialog(self.dialog, record.profile.to_json_data(), "カスタム形式を編集")
        profile = editor.show()
        if profile is None:
            return
        try:
            if profile.profile_id == original_id:
                save_profile(replace(profile, path=record.path), record.path)
            else:
                register_profile(profile)
                delete_registered_profile(original_id)
        except ProfileError as exc:
            self.app._append_log(f"カスタム形式の保存エラー: {exc}")
            self.app._record_failure("カスタム形式を保存できませんでした。詳細を確認してください。")
            messagebox.showerror("保存エラー", str(exc), parent=self.dialog)
            return
        self._refresh_after_change()
        self.app._append_log(f"カスタム形式を保存しました: {profile.profile_id}")
        self.app._clear_diagnostics()
        self.app._set_result_status("カスタム形式を保存しました。")

    def duplicate_profile(self) -> None:
        record = self._selected_record()
        if record is None or record.profile is None:
            return
        data = record.profile.to_json_data()
        data["profile_id"] = self._unique_copy_id(record.profile.profile_id)
        data["name"] = f"{record.profile.name} コピー"
        editor = ProfileEditorDialog(self.dialog, data, "カスタム形式を複製")
        profile = editor.show()
        if profile is None:
            return
        try:
            register_profile(profile)
        except ProfileError as exc:
            self.app._append_log(f"カスタム形式の複製エラー: {exc}")
            self.app._record_failure("カスタム形式を複製できませんでした。詳細を確認してください。")
            messagebox.showerror("保存エラー", str(exc), parent=self.dialog)
            return
        self._refresh_after_change()
        self.app._append_log(f"カスタム形式を複製しました: {profile.profile_id}")
        self.app._clear_diagnostics()
        self.app._set_result_status("カスタム形式を登録しました。")

    def validate_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        validation = validate_profile_file(record.path)
        if validation.is_valid:
            self.app._append_log(f"カスタム形式の検証に成功しました: {record.path}")
            self.app._clear_diagnostics()
            self.app._set_result_status("カスタム形式の検証が完了しました。")
            messagebox.showinfo("検証結果", "エラーはありません。", parent=self.dialog)
            return
        self.app._append_log(f"カスタム形式の検証に失敗しました: {record.path}")
        for issue in validation.issues:
            self.app._append_log(issue.format(str(record.path)))
        self.app._record_failure("カスタム形式の検証に失敗しました。詳細を確認してください。")
        messagebox.showerror(
            "検証結果",
            "\n".join(issue.format(str(record.path)) for issue in validation.issues),
            parent=self.dialog,
        )

    def enable_selected(self) -> None:
        self._set_selected_enabled(True)

    def disable_selected(self) -> None:
        self._set_selected_enabled(False)

    def _set_selected_enabled(self, enabled: bool) -> None:
        record = self._selected_record()
        if record is None or record.profile is None:
            return
        try:
            set_registered_profile_enabled(record.profile.profile_id, enabled)
        except ProfileError as exc:
            self.app._append_log(f"カスタム形式の登録状態変更エラー: {exc}")
            self.app._record_failure("カスタム形式の登録状態を変更できませんでした。詳細を確認してください。")
            messagebox.showerror("登録状態の変更エラー", str(exc), parent=self.dialog)
            return
        self._refresh_after_change()
        action = "有効化" if enabled else "無効化"
        self.app._append_log(f"カスタム形式を{action}しました: {record.profile.profile_id}")
        self.app._clear_diagnostics()
        self.app._set_result_status(f"カスタム形式を{action}しました。")

    def import_profile(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.dialog,
            title="カスタム形式プロファイルをインポート",
            filetypes=[("RubiMorph profile", f"*{PROFILE_EXTENSION}"), ("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            import_profile_file(path)
        except ProfileError as exc:
            if "既に登録" not in str(exc):
                self.app._append_log(f"カスタム形式のインポートエラー: {exc}")
                self.app._record_failure("カスタム形式をインポートできませんでした。詳細を確認してください。")
                messagebox.showerror("インポートエラー", str(exc), parent=self.dialog)
                return
            if not messagebox.askyesno("上書き確認", f"{exc}\n上書きしますか。", parent=self.dialog):
                return
            try:
                import_profile_file(path, overwrite=True)
            except ProfileError as retry_exc:
                self.app._append_log(f"カスタム形式のインポートエラー: {retry_exc}")
                self.app._record_failure("カスタム形式をインポートできませんでした。詳細を確認してください。")
                messagebox.showerror("インポートエラー", str(retry_exc), parent=self.dialog)
                return
        self._refresh_after_change()
        self.app._append_log(f"カスタム形式をインポートしました: {path}")
        self.app._clear_diagnostics()
        self.app._set_result_status("カスタム形式をインポートしました。")

    def export_profile(self) -> None:
        record = self._selected_record()
        if record is None or record.profile is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="カスタム形式プロファイルをエクスポート",
            defaultextension=PROFILE_EXTENSION,
            initialfile=f"{record.profile.profile_id}{PROFILE_EXTENSION}",
            filetypes=[("RubiMorph profile", f"*{PROFILE_EXTENSION}"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            export_registered_profile(record.profile.profile_id, path)
        except ProfileError as exc:
            self.app._append_log(f"カスタム形式のエクスポートエラー: {exc}")
            self.app._record_failure("カスタム形式をエクスポートできませんでした。詳細を確認してください。")
            messagebox.showerror("エクスポートエラー", str(exc), parent=self.dialog)
            return
        self.app._append_log(f"カスタム形式をエクスポートしました: {path}")
        self.app._clear_diagnostics()
        self.app._set_result_status("カスタム形式をエクスポートしました。")

    def delete_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        label = record.profile.name if record.profile else record.path.name
        if not messagebox.askyesno("削除確認", f"{label} を削除しますか。", parent=self.dialog):
            return
        try:
            if record.profile:
                delete_registered_profile(record.profile.profile_id)
            else:
                record.path.unlink()
        except (OSError, ProfileError) as exc:
            self.app._append_log(f"カスタム形式の登録解除エラー: {exc}")
            self.app._record_failure("カスタム形式の登録を解除できませんでした。詳細を確認してください。")
            messagebox.showerror("削除エラー", str(exc), parent=self.dialog)
            return
        self._refresh_after_change()
        self.app._append_log(f"カスタム形式の登録を解除しました: {label}")
        self.app._clear_diagnostics()
        self.app._set_result_status("カスタム形式の登録を解除しました。")

    def save_selected(self) -> None:
        record = self._selected_record()
        if record is None or record.profile is None:
            return
        try:
            save_profile(record.profile, record.path)
        except ProfileError as exc:
            self.app._append_log(f"カスタム形式の保存エラー: {exc}")
            self.app._record_failure("カスタム形式を保存できませんでした。詳細を確認してください。")
            messagebox.showerror("保存エラー", str(exc), parent=self.dialog)
            return
        self._refresh_after_change()
        self.app._append_log(f"カスタム形式を保存しました: {record.profile.profile_id}")
        self.app._clear_diagnostics()
        self.app._set_result_status("カスタム形式を保存しました。")

    def save_selected_as(self) -> None:
        record = self._selected_record()
        if record is None or record.profile is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="名前を付けて保存",
            defaultextension=PROFILE_EXTENSION,
            initialfile=f"{record.profile.profile_id}{PROFILE_EXTENSION}",
            filetypes=[("RubiMorph profile", f"*{PROFILE_EXTENSION}"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            save_profile(record.profile, path)
        except ProfileError as exc:
            messagebox.showerror("保存エラー", str(exc), parent=self.dialog)

    def _unique_copy_id(self, profile_id: str) -> str:
        existing = {
            record.profile.profile_id
            for record in load_registered_profiles()
            if record.profile is not None
        }
        base = f"{profile_id}-copy"
        if base not in existing:
            return base
        index = 2
        while f"{base}-{index}" in existing:
            index += 1
        return f"{base}-{index}"


class ProfileEditorDialog:
    def __init__(self, parent: tk.Misc, data: dict[str, Any], title: str) -> None:
        self.parent = parent
        self.data = json.loads(json.dumps(data, ensure_ascii=False))
        self.result: CustomFormatProfile | None = None
        self.parser_rules: list[dict[str, Any]] = list(self.data.get("parser", {}).get("rules", []))
        transforms = self.data.get("transforms", {})
        self.before_rules: list[dict[str, Any]] = list(transforms.get("before_parse", []))
        self.after_rules: list[dict[str, Any]] = list(transforms.get("after_render", []))

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)
        self.dialog.geometry("980x720")
        self.dialog.minsize(820, 560)
        self.dialog.rowconfigure(0, weight=1)
        self.dialog.columnconfigure(0, weight=1)

        self.profile_id_var = tk.StringVar(value=self.data.get("profile_id", ""))
        self.name_var = tk.StringVar(value=self.data.get("name", ""))
        self.enabled_var = tk.BooleanVar(value=self.data.get("enabled", True))
        capabilities = self.data.get("capabilities", {})
        self.input_capability_var = tk.BooleanVar(value=capabilities.get("input", True))
        self.output_capability_var = tk.BooleanVar(value=capabilities.get("output", True))
        templates = self.data.get("renderer", {}).get("templates", {})
        self.ruby_template_var = tk.StringVar(value=templates.get("ruby", "[[ruby:{base}|{reading}]]"))
        self.emphasis_template_var = tk.StringVar(value=templates.get("emphasis", "[[em:{text}]]"))

        self._build()

    def show(self) -> CustomFormatProfile | None:
        self.dialog.grab_set()
        self.parent.wait_window(self.dialog)
        return self.result

    def _build(self) -> None:
        notebook = ttk.Notebook(self.dialog)
        notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self._build_basic_tab(notebook)
        self.parser_editor = ParserRuleEditorFrame(notebook, self.parser_rules)
        notebook.add(self.parser_editor.frame, text="入力規則")
        self._build_template_tab(notebook)
        self.before_editor = TransformRuleEditorFrame(notebook, self.before_rules, "before_parse")
        notebook.add(self.before_editor.frame, text="前処理")
        self.after_editor = TransformRuleEditorFrame(notebook, self.after_rules, "after_render")
        notebook.add(self.after_editor.frame, text="後処理")
        self._build_test_tab(notebook)

        buttons = ttk.Frame(self.dialog, padding=(10, 0, 10, 10))
        buttons.grid(row=1, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        ttk.Button(buttons, text="検証", command=lambda: self.validate(show_dialog=True)).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(buttons, text="保存", command=self.save).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(buttons, text="キャンセル", command=self.dialog.destroy).grid(row=0, column=3)

    def _build_basic_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        frame.columnconfigure(1, weight=1)
        notebook.add(frame, text="基本情報")

        ttk.Label(frame, text="表示名").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", pady=(0, 6))
        ttk.Label(frame, text="プロファイルID").grid(row=1, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.profile_id_var).grid(row=1, column=1, sticky="ew", pady=(0, 6))
        ttk.Label(frame, text="説明").grid(row=2, column=0, sticky="nw", pady=(0, 6))
        self.description_text = tk.Text(frame, height=5, wrap=tk.WORD)
        self.description_text.insert("1.0", self.data.get("description", ""))
        self.description_text.grid(row=2, column=1, sticky="ew", pady=(0, 6))
        ttk.Checkbutton(frame, text="登録状態を有効にする", variable=self.enabled_var).grid(
            row=3, column=1, sticky="w", pady=(4, 0)
        )
        ttk.Checkbutton(frame, text="入力形式として使用", variable=self.input_capability_var).grid(
            row=4, column=1, sticky="w", pady=(4, 0)
        )
        ttk.Checkbutton(frame, text="出力形式として使用", variable=self.output_capability_var).grid(
            row=5, column=1, sticky="w", pady=(4, 0)
        )

    def _build_template_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        frame.columnconfigure(1, weight=1)
        notebook.add(frame, text="出力テンプレート")
        monospace = ("Consolas", 10)

        ttk.Label(frame, text="ルビ").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.ruby_template_var, font=monospace).grid(
            row=0, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(frame, text="使用可能: {base}, {reading} / 波括弧: {{ と }}").grid(
            row=1, column=1, sticky="w", pady=(0, 12)
        )
        ttk.Label(frame, text="傍点").grid(row=2, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.emphasis_template_var, font=monospace).grid(
            row=2, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(frame, text="使用可能: {text} / 波括弧: {{ と }}").grid(row=3, column=1, sticky="w")

    def _build_test_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(0, weight=1)
        notebook.add(frame, text="検証とテスト")

        ttk.Label(frame, text="テスト入力").grid(row=0, column=0, sticky="w")
        self.test_input = scrolledtext.ScrolledText(frame, height=6, wrap=tk.WORD)
        self.test_input.insert("1.0", "[[ruby:親文字|ルビ]] と [[em:傍点対象]]")
        self.test_input.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(actions, text="検証", command=lambda: self.validate(show_dialog=True)).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(actions, text="テスト実行", command=self.run_test).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(actions, text="テスト処理をキャンセル", command=self.cancel_test).grid(row=0, column=2)

        self.test_output = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        self.test_output.grid(row=3, column=0, sticky="nsew")

    def _build_data(self) -> dict[str, Any]:
        capabilities = {
            "input": bool(self.input_capability_var.get()),
            "output": bool(self.output_capability_var.get()),
        }
        data: dict[str, Any] = {
            "schema_version": 1,
            "profile_id": self.profile_id_var.get().strip(),
            "name": self.name_var.get().strip(),
            "description": self.description_text.get("1.0", "end-1c"),
            "enabled": bool(self.enabled_var.get()),
            "capabilities": capabilities,
        }
        if capabilities["input"]:
            data["parser"] = {"rules": self.parser_editor.rules}
        if capabilities["output"]:
            data["renderer"] = {
                "templates": {
                    "ruby": self.ruby_template_var.get(),
                    "emphasis": self.emphasis_template_var.get(),
                }
            }
        transforms: dict[str, Any] = {}
        if self.before_editor.rules:
            transforms["before_parse"] = self.before_editor.rules
        if self.after_editor.rules:
            transforms["after_render"] = self.after_editor.rules
        if transforms:
            data["transforms"] = transforms
        return data

    def validate(self, *, show_dialog: bool) -> bool:
        result = validate_profile_data(self._build_data())
        message = (
            "エラーはありません。"
            if result.is_valid
            else "\n".join(issue.format() for issue in result.issues)
        )
        self._set_test_output(message)
        if show_dialog:
            if result.is_valid:
                messagebox.showinfo("検証結果", message, parent=self.dialog)
            else:
                messagebox.showerror("検証結果", message, parent=self.dialog)
        return result.is_valid

    def save(self) -> None:
        data = self._build_data()
        result = validate_profile_data(data)
        if not result.is_valid:
            self._set_test_output("\n".join(issue.format() for issue in result.issues))
            messagebox.showerror("検証エラー", "エラーがあるため保存できません。", parent=self.dialog)
            return
        self.result = profile_from_data(data)
        self.dialog.destroy()

    def run_test(self) -> None:
        data = self._build_data()
        result = validate_profile_data(data)
        if not result.is_valid:
            self._set_test_output("\n".join(issue.format() for issue in result.issues))
            return
        profile = profile_from_data(data)
        try:
            if profile.capabilities.input and profile.capabilities.output:
                conversion = convert_text_flexible(
                    self.test_input.get("1.0", "end-1c"),
                    source_profile=profile,
                    target_profile=profile,
                )
                output = [
                    "解析結果:",
                    _format_tokens(conversion.tokens),
                    "",
                    "テスト出力:",
                    conversion.output,
                ]
            elif profile.capabilities.input:
                tokens = parse_custom_tokens(profile, self.test_input.get("1.0", "end-1c"))
                output = ["解析結果:", _format_tokens(tokens)]
            else:
                tokens = [
                    TextToken("これは"),
                    RubyToken(base="親文字", ruby="ルビ"),
                    TextToken("と"),
                    EmphasisToken(value="傍点対象"),
                    TextToken("です。"),
                ]
                output = ["テスト出力:", render_custom_tokens(profile, tokens)]
        except Exception as exc:  # noqa: BLE001
            self._set_test_output(f"テストエラー: {exc}")
            return
        self._set_test_output("\n".join(output))

    def cancel_test(self) -> None:
        self._set_test_output("現在の実装ではテスト処理は短いタイムアウト付きで実行されます。実行中の長時間処理は core 側で停止します。")

    def _set_test_output(self, text: str) -> None:
        self.test_output.delete("1.0", tk.END)
        self.test_output.insert("1.0", text)


class ParserRuleEditorFrame:
    def __init__(self, parent: ttk.Notebook, rules: list[dict[str, Any]]) -> None:
        self.rules = rules
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        columns = ("id", "name", "kind", "priority", "enabled", "pattern", "flags")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", selectmode="browse")
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=120 if column != "pattern" else 320)
        self.tree.grid(row=0, column=0, sticky="nsew")
        buttons = ttk.Frame(self.frame)
        buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        actions = [
            ("規則追加", self.add),
            ("規則編集", self.edit),
            ("規則削除", self.delete),
            ("規則複製", self.duplicate),
            ("上へ移動", lambda: self.move(-1)),
            ("下へ移動", lambda: self.move(1)),
        ]
        for index, (label, command) in enumerate(actions):
            ttk.Button(buttons, text=label, command=command).grid(row=0, column=index, padx=(0, 6))
        self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for index, rule in enumerate(self.rules):
            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    rule.get("id", ""),
                    rule.get("name", ""),
                    rule.get("kind", ""),
                    rule.get("priority", 0),
                    "有効" if rule.get("enabled", True) else "無効",
                    rule.get("pattern", ""),
                    ", ".join(rule.get("flags", [])),
                ),
            )

    def selected_index(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def add(self) -> None:
        rule = ParserRuleDialog(self.frame, _default_parser_rule()).show()
        if rule is None:
            return
        self.rules.append(rule)
        self.refresh()

    def edit(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        rule = ParserRuleDialog(self.frame, self.rules[index]).show()
        if rule is None:
            return
        self.rules[index] = rule
        self.refresh()

    def delete(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        del self.rules[index]
        self.refresh()

    def duplicate(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        rule = dict(self.rules[index])
        rule["id"] = f"{rule.get('id', 'rule')}-copy"
        self.rules.insert(index + 1, rule)
        self.refresh()

    def move(self, delta: int) -> None:
        index = self.selected_index()
        if index is None:
            return
        new_index = index + delta
        if new_index < 0 or new_index >= len(self.rules):
            return
        self.rules[index], self.rules[new_index] = self.rules[new_index], self.rules[index]
        self.refresh()
        self.tree.selection_set(str(new_index))


class TransformRuleEditorFrame:
    def __init__(self, parent: ttk.Notebook, rules: list[dict[str, Any]], position: str) -> None:
        self.rules = rules
        self.position = position
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        columns = ("id", "name", "type", "enabled", "pattern", "replacement", "flags")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", selectmode="browse")
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=120 if column not in {"pattern", "replacement"} else 260)
        self.tree.grid(row=0, column=0, sticky="nsew")
        buttons = ttk.Frame(self.frame)
        buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        actions = [
            ("規則追加", self.add),
            ("規則編集", self.edit),
            ("規則削除", self.delete),
            ("規則複製", self.duplicate),
            ("上へ移動", lambda: self.move(-1)),
            ("下へ移動", lambda: self.move(1)),
        ]
        for index, (label, command) in enumerate(actions):
            ttk.Button(buttons, text=label, command=command).grid(row=0, column=index, padx=(0, 6))
        self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for index, rule in enumerate(self.rules):
            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    rule.get("id", ""),
                    rule.get("name", ""),
                    rule.get("type", ""),
                    "有効" if rule.get("enabled", True) else "無効",
                    rule.get("pattern", ""),
                    rule.get("replacement", ""),
                    ", ".join(rule.get("flags", [])),
                ),
            )

    def selected_index(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def add(self) -> None:
        rule = TransformRuleDialog(self.frame, _default_transform_rule()).show()
        if rule is None:
            return
        self.rules.append(rule)
        self.refresh()

    def edit(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        rule = TransformRuleDialog(self.frame, self.rules[index]).show()
        if rule is None:
            return
        self.rules[index] = rule
        self.refresh()

    def delete(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        del self.rules[index]
        self.refresh()

    def duplicate(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        rule = dict(self.rules[index])
        rule["id"] = f"{rule.get('id', 'rule')}-copy"
        self.rules.insert(index + 1, rule)
        self.refresh()

    def move(self, delta: int) -> None:
        index = self.selected_index()
        if index is None:
            return
        new_index = index + delta
        if new_index < 0 or new_index >= len(self.rules):
            return
        self.rules[index], self.rules[new_index] = self.rules[new_index], self.rules[index]
        self.refresh()
        self.tree.selection_set(str(new_index))


class ParserRuleDialog:
    def __init__(self, parent: tk.Misc, rule: dict[str, Any]) -> None:
        self.parent = parent
        self.rule = dict(rule)
        self.result: dict[str, Any] | None = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("入力規則")
        self.dialog.transient(parent)
        self.dialog.columnconfigure(1, weight=1)
        self.id_var = tk.StringVar(value=self.rule.get("id", ""))
        self.name_var = tk.StringVar(value=self.rule.get("name", ""))
        self.kind_var = tk.StringVar(value=self.rule.get("kind", "ruby"))
        self.priority_var = tk.StringVar(value=str(self.rule.get("priority", 100)))
        self.enabled_var = tk.BooleanVar(value=self.rule.get("enabled", True))
        self.flags_var = tk.StringVar(value=", ".join(self.rule.get("flags", [])))
        self._build()

    def show(self) -> dict[str, Any] | None:
        self.dialog.grab_set()
        self.parent.wait_window(self.dialog)
        return self.result

    def _build(self) -> None:
        fields = [
            ("規則ID", ttk.Entry(self.dialog, textvariable=self.id_var)),
            ("規則名", ttk.Entry(self.dialog, textvariable=self.name_var)),
            ("kind", ttk.Combobox(self.dialog, textvariable=self.kind_var, values=["ruby", "emphasis"], state="readonly")),
            ("priority", ttk.Entry(self.dialog, textvariable=self.priority_var)),
            ("flags", ttk.Entry(self.dialog, textvariable=self.flags_var)),
        ]
        for row, (label, widget) in enumerate(fields):
            ttk.Label(self.dialog, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=(8, 0))
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=(8, 0))
        ttk.Checkbutton(self.dialog, text="有効", variable=self.enabled_var).grid(
            row=5, column=1, sticky="w", padx=10, pady=(8, 0)
        )
        ttk.Label(self.dialog, text="正規表現").grid(row=6, column=0, sticky="nw", padx=10, pady=(8, 0))
        self.pattern_text = tk.Text(self.dialog, width=72, height=5, font=("Consolas", 10))
        self.pattern_text.insert("1.0", self.rule.get("pattern", ""))
        self.pattern_text.grid(row=6, column=1, sticky="ew", padx=10, pady=(8, 0))
        buttons = ttk.Frame(self.dialog)
        buttons.grid(row=7, column=0, columnspan=2, sticky="e", padx=10, pady=10)
        ttk.Button(buttons, text="OK", command=self.ok).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="キャンセル", command=self.dialog.destroy).grid(row=0, column=1)

    def ok(self) -> None:
        try:
            priority = int(self.priority_var.get())
        except ValueError:
            messagebox.showerror("入力エラー", "priority は整数です。", parent=self.dialog)
            return
        self.result = {
            "id": self.id_var.get().strip(),
            "name": self.name_var.get().strip(),
            "kind": self.kind_var.get(),
            "enabled": bool(self.enabled_var.get()),
            "priority": priority,
            "pattern": self.pattern_text.get("1.0", "end-1c"),
            "flags": _split_flags(self.flags_var.get()),
        }
        self.dialog.destroy()


class TransformRuleDialog:
    def __init__(self, parent: tk.Misc, rule: dict[str, Any]) -> None:
        self.parent = parent
        self.rule = dict(rule)
        self.result: dict[str, Any] | None = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("置換規則")
        self.dialog.transient(parent)
        self.dialog.columnconfigure(1, weight=1)
        self.id_var = tk.StringVar(value=self.rule.get("id", ""))
        self.name_var = tk.StringVar(value=self.rule.get("name", ""))
        self.type_var = tk.StringVar(value=self.rule.get("type", "literal"))
        self.enabled_var = tk.BooleanVar(value=self.rule.get("enabled", True))
        self.flags_var = tk.StringVar(value=", ".join(self.rule.get("flags", [])))
        self._build()

    def show(self) -> dict[str, Any] | None:
        self.dialog.grab_set()
        self.parent.wait_window(self.dialog)
        return self.result

    def _build(self) -> None:
        fields = [
            ("規則ID", ttk.Entry(self.dialog, textvariable=self.id_var)),
            ("規則名", ttk.Entry(self.dialog, textvariable=self.name_var)),
            ("type", ttk.Combobox(self.dialog, textvariable=self.type_var, values=["literal", "regex"], state="readonly")),
            ("flags", ttk.Entry(self.dialog, textvariable=self.flags_var)),
        ]
        for row, (label, widget) in enumerate(fields):
            ttk.Label(self.dialog, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=(8, 0))
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=(8, 0))
        ttk.Checkbutton(self.dialog, text="有効", variable=self.enabled_var).grid(
            row=4, column=1, sticky="w", padx=10, pady=(8, 0)
        )
        ttk.Label(self.dialog, text="pattern").grid(row=5, column=0, sticky="nw", padx=10, pady=(8, 0))
        self.pattern_text = tk.Text(self.dialog, width=72, height=4, font=("Consolas", 10))
        self.pattern_text.insert("1.0", self.rule.get("pattern", ""))
        self.pattern_text.grid(row=5, column=1, sticky="ew", padx=10, pady=(8, 0))
        ttk.Label(self.dialog, text="replacement").grid(row=6, column=0, sticky="nw", padx=10, pady=(8, 0))
        self.replacement_text = tk.Text(self.dialog, width=72, height=4, font=("Consolas", 10))
        self.replacement_text.insert("1.0", self.rule.get("replacement", ""))
        self.replacement_text.grid(row=6, column=1, sticky="ew", padx=10, pady=(8, 0))
        buttons = ttk.Frame(self.dialog)
        buttons.grid(row=7, column=0, columnspan=2, sticky="e", padx=10, pady=10)
        ttk.Button(buttons, text="OK", command=self.ok).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="キャンセル", command=self.dialog.destroy).grid(row=0, column=1)

    def ok(self) -> None:
        self.result = {
            "id": self.id_var.get().strip(),
            "name": self.name_var.get().strip(),
            "enabled": bool(self.enabled_var.get()),
            "type": self.type_var.get(),
            "pattern": self.pattern_text.get("1.0", "end-1c"),
            "replacement": self.replacement_text.get("1.0", "end-1c"),
            "flags": _split_flags(self.flags_var.get()),
        }
        self.dialog.destroy()


def _default_profile_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "profile_id": "my-format",
        "name": "My Format",
        "description": "",
        "enabled": True,
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
        "transforms": {"before_parse": [], "after_render": []},
    }


def _default_parser_rule() -> dict[str, Any]:
    return {
        "id": "rule",
        "name": "",
        "kind": "ruby",
        "enabled": True,
        "priority": 100,
        "pattern": r"(?P<base>.+?)\|(?P<reading>.+?)",
        "flags": [],
    }


def _default_transform_rule() -> dict[str, Any]:
    return {
        "id": "replace",
        "name": "",
        "enabled": True,
        "type": "literal",
        "pattern": "",
        "replacement": "",
        "flags": [],
    }


def _split_flags(value: str) -> list[str]:
    return [item for item in re.split(r"[\s,]+", value.strip()) if item]


def _format_tokens(tokens) -> str:
    lines: list[str] = []
    for token in tokens:
        if isinstance(token, TextToken):
            lines.append(f"text: {token.value!r}")
        elif isinstance(token, RubyToken):
            lines.append(f"ruby: base={token.base!r}, reading={token.ruby!r}")
        elif isinstance(token, EmphasisToken):
            lines.append(f"emphasis: text={token.value!r}")
        else:
            lines.append(f"{type(token).__name__}: {token!r}")
    return "\n".join(lines)


def _resource_path(relative_path: Path) -> Path:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "executable"):
        candidates.append(Path(sys.executable).resolve().parent / relative_path)

    pyinstaller_root = getattr(sys, "_MEIPASS", None)
    if pyinstaller_root:
        candidates.append(Path(pyinstaller_root) / relative_path)

    candidates.append(ROOT_DIR / relative_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _run_cli_mode(argv: list[str]) -> int:
    from rubimorph.platform_profiles import PLATFORM_PROFILES, list_platform_profiles

    if "--version" in argv:
        print(f"{APP_NAME} {__version__}")
        return 0

    if "--list-platforms" in argv:
        print("platform\tlabel\tstatus\tverification")
        for profile in list_platform_profiles():
            print(
                f"{profile.platform_id}\t{profile.label}\t{profile.status}\t{profile.verification_status}"
            )
        return 0

    if "--matrix" in argv:
        print("source -> target\truby\temphasis\tnote")
        for source in list_platform_profiles():
            for target in list_platform_profiles():
                if source.platform_id == target.platform_id:
                    state = "not-applicable"
                elif source.status in {"research-needed", "unsupported"}:
                    state = "research-needed"
                elif target.status in {"research-needed", "unsupported", "planned"}:
                    state = "warning-required"
                elif target.platform_id in {"plain", "markdown"}:
                    state = "lossy"
                else:
                    state = "partial" if "emphasis" not in target.output_markup else "supported"
                emphasis_state = "yes" if "emphasis" in target.output_markup else "warning"
                print(
                    f"{source.platform_id} -> {target.platform_id}\t{state}\t{emphasis_state}\t{target.status}"
                )
        return 0

    if "--help" in argv or "-h" in argv:
        print(f"{APP_NAME} {__version__}")
        print("GUI: RubiMorphGUI.exe")
        print("CLI: RubiMorph.exe --version | --list-platforms | --matrix")
        print('CLI sample: RubiMorph.exe --from kakuyomu --to pixiv --text "｜空《そら》"')
        return 0

    if "--from" in argv and "--to" in argv and "--text" in argv:
        try:
            source = argv[argv.index("--from") + 1]
            target = argv[argv.index("--to") + 1]
            text = argv[argv.index("--text") + 1]
        except IndexError:
            print("missing value for --from, --to, or --text", file=sys.stderr)
            return 2
        if source not in PLATFORM_PROFILES or target not in PLATFORM_PROFILES:
            print("unsupported platform", file=sys.stderr)
            return 2
        result = convert_text(source, target, text, RenderOptions())
        print(result.output)
        for diagnostic in result.diagnostics:
            print(
                f"[{diagnostic.level.upper()}] {diagnostic.code}: {diagnostic.message}",
                file=sys.stderr,
            )
        return 0

    print("unsupported arguments. Use --help for CLI options.", file=sys.stderr)
    return 2


def launch_gui() -> None:
    _configure_stdio()
    _set_windows_app_user_model_id()
    root = Tk()
    RubiMorphApp(root)
    root.mainloop()


def main() -> None:
    _configure_stdio()
    _set_windows_app_user_model_id()
    if len(sys.argv) > 1:
        raise SystemExit(_run_cli_mode(sys.argv[1:]))

    launch_gui()


if __name__ == "__main__":
    main()
