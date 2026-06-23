# Third Party Notices

This file summarizes third-party software relevant to RubiMorph Windows distributions.

RubiMorph itself is licensed under the MIT License. See `LICENSE`.

## Role of this file and LICENSES/

- `THIRD_PARTY_NOTICES.md`: component summary, purpose, version, and distribution status.
- `LICENSES/`: license texts obtained from the actual local build environment or installed package metadata.

Both files are included in the PyInstaller output, installer, portable ZIP, and GitHub Release assets.

## Runtime components bundled in Windows distributions

| Component | Version used for this release | Purpose | Bundled in app folder | License text |
| --- | --- | --- | --- | --- |
| Python | 3.14.3 x64 | Python runtime, standard library, DLLs, and extension modules bundled by PyInstaller | Yes | `LICENSES/Python-3.14.3-LICENSE.txt` |
| Tk/Tcl runtime used by Tkinter | 8.6 | GUI toolkit runtime files bundled through Python/Tkinter/PyInstaller | Yes | `LICENSES/Tk-8.6-license.terms`; Python's `LICENSE.txt` also notes Tcl/Tk-derived components |
| PyInstaller bootloader and runtime hooks | 6.20.0 | Bootloader and packaging runtime used by `RubiMorph.exe` and `RubiMorphGUI.exe` | Embedded/generated | `LICENSES/PyInstaller-6.20.0-COPYING.txt` |
| Inno Setup generated setup/uninstaller runtime | 7.x | Installer and uninstaller runtime code for `RubiMorphSetup-<VERSION>.exe` | Installer only | `LICENSES/Inno-Setup-7-license.txt` |

Python's license text also covers several third-party components distributed with the official Python Windows runtime, including DLLs and libraries noted in Python's `LICENSE.txt`. The local Python installation used for this release includes Tk 8.6 `license.terms`; a separate `license.tcltk` file was not present in that installation.

## Build-time tools

These tools are used to build or describe releases. They are not imported by RubiMorph at runtime and are not intended to be bundled as application libraries.

| Tool | Version pinned or observed | Purpose | Runtime bundled |
| --- | --- | --- | --- |
| PyInstaller | 6.20.0 | Build GUI and CLI executables | Bootloader/runtime parts only |
| pyinstaller-hooks-contrib | 2026.6 | PyInstaller build hooks | No |
| cyclonedx-bom | 7.3.0 | Generate CycloneDX SBOM from `requirements-build.txt` | No |
| Inno Setup Compiler | 7.x | Build Windows installer | Generated installer runtime only |

The SBOM for release assets is generated from `requirements-build.txt` and may include build-time Python packages and their transitive dependencies. The SBOM and this notice serve different purposes: the SBOM is machine-readable dependency metadata, while this file is the human-readable distribution notice.

## Review sources used for 1.0.0

- Python license text: `LICENSE.txt` from the Python 3.14.3 x64 distribution used for the local build.
- Tk 8.6 license terms: `tcl/tk8.6/license.terms` from the same Python 3.14.3 distribution.
- PyInstaller license text: installed wheel metadata at `pyinstaller-6.20.0.dist-info/licenses/COPYING.txt`
- Inno Setup license text: `C:\Program Files\Inno Setup 7\license.txt`
- Build dependency versions: `requirements-build.txt` and installed package metadata

When Python, Tk/Tcl, PyInstaller, Inno Setup, build dependencies, PyInstaller settings, or bundled release contents change, refresh this file, `LICENSES/`, the GUI OSS license view, installer and portable ZIP contents, and the SBOM together.
