"""GUI-only entry point for the RubiMorph Windows launcher."""

from __future__ import annotations

import traceback
import tkinter as tk
from multiprocessing import freeze_support
from tkinter import messagebox


def main() -> int:
    try:
        from app import launch_gui

        launch_gui()
    except Exception as exc:  # noqa: BLE001
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "RubiMorph 起動エラー",
            "RubiMorphのGUIを起動できませんでした。\n\n"
            f"{exc}\n\n"
            f"{traceback.format_exc()}",
        )
        root.destroy()
        return 1
    return 0


if __name__ == "__main__":
    freeze_support()
    raise SystemExit(main())
