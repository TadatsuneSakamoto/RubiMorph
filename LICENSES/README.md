# LICENSES

This directory stores license texts for third-party components that are relevant to RubiMorph Windows binary distributions.

`THIRD_PARTY_NOTICES.md` is the human-readable summary: component name, purpose, version, and whether it is bundled in the installer or portable ZIP.

`LICENSES/` stores the corresponding license text files obtained from the actual local build environment or installed package metadata used for the release.

Current files:

- `Python-3.14.3-LICENSE.txt`
  Python runtime license text from `LICENSE.txt` in the Python 3.14.3 x64 distribution used for the local build.
- `Tk-8.6-license.terms`
  Tk 8.6 license terms from the Python runtime's bundled Tk files. The local Python installation used for this release did not include a separate `license.tcltk`; Python's `LICENSE.txt` also notes Tcl/Tk-derived components.
- `PyInstaller-6.20.0-COPYING.txt`
  PyInstaller license text from the installed PyInstaller wheel metadata.
- `Inno-Setup-7-license.txt`
  Inno Setup 7 license text from the local compiler installation.

When the Python, Tk/Tcl, PyInstaller, Inno Setup, or release build environment changes, refresh these files from the actual build inputs and update `THIRD_PARTY_NOTICES.md`, the GUI OSS license view, the installer, the portable ZIP, and the SBOM together.
