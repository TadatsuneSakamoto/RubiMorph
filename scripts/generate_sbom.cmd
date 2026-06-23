@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

if not exist requirements-build.txt goto no_requirements
if not exist dist\sbom mkdir dist\sbom

set PYTHONUTF8=1

where py >nul 2>nul
if not errorlevel 1 goto use_py

where python >nul 2>nul
if not errorlevel 1 goto use_python

where cyclonedx-py >nul 2>nul
if not errorlevel 1 goto use_exe

goto no_tool

:use_py
py -3 -m cyclonedx_py requirements requirements-build.txt --output-format JSON --output-file dist\sbom\rubimorph.cdx.json
exit /b %ERRORLEVEL%

:use_python
python -m cyclonedx_py requirements requirements-build.txt --output-format JSON --output-file dist\sbom\rubimorph.cdx.json
exit /b %ERRORLEVEL%

:use_exe
cyclonedx-py requirements requirements-build.txt --output-format JSON --output-file dist\sbom\rubimorph.cdx.json
exit /b %ERRORLEVEL%

:no_tool
echo cyclonedx-py または python -m cyclonedx_py が見つかりません。SBOM生成手順は docs\sbom.md を確認してください。
echo 例: py -3 -m pip install cyclonedx-bom
exit /b 1

:no_requirements
echo requirements-build.txt が見つかりません。SBOMを生成できません。
exit /b 1
