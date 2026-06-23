# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

SPEC_PATH = (
    Path(__file__).resolve()
    if "__file__" in globals()
    else Path.cwd() / "installer" / "pyinstaller" / "rubimorph.spec"
)
ROOT = SPEC_PATH.parents[2]
ICON_FILE = ROOT / "assets" / "icons" / "rubimorph.ico"
VERSION_FILE = ROOT / "VERSION"
CLI_ENTRY = ROOT / "installer" / "pyinstaller" / "rubimorph_cli.py"
GUI_ENTRY = ROOT / "src" / "desktop" / "rubimorph_gui.py"
DATA_FILES = [
    (str(VERSION_FILE), "."),
    (str(ICON_FILE), "assets/icons"),
]
for relative in ("docs", "examples", "schemas"):
    source = ROOT / relative
    if source.exists():
        DATA_FILES.append((str(source), relative))

a = Analysis(
    [str(CLI_ENTRY), str(GUI_ENTRY)],
    pathex=[str(ROOT / "src" / "core"), str(ROOT / "src" / "desktop")],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=["rubimorph"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

runtime_hooks = [entry for entry in a.scripts if entry[0].startswith("pyi_rth_")]


def script_entries(name):
    matches = [entry for entry in a.scripts if entry[0] == name]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one PyInstaller script entry for {name}, got {len(matches)}")
    return runtime_hooks + matches


cli_scripts = script_entries("rubimorph_cli")
gui_scripts = script_entries("rubimorph_gui")

cli_exe = EXE(
    pyz,
    cli_scripts,
    [],
    exclude_binaries=True,
    name="RubiMorph",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_FILE),
)

gui_exe = EXE(
    pyz,
    gui_scripts,
    [],
    exclude_binaries=True,
    name="RubiMorphGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_FILE),
)

coll = COLLECT(
    cli_exe,
    gui_exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RubiMorph",
)
