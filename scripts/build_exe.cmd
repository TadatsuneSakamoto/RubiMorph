@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m PyInstaller --version >nul 2>nul
if errorlevel 1 goto no_pyinstaller
py -3 -m PyInstaller --noconfirm installer\pyinstaller\rubimorph.spec
if errorlevel 1 exit /b %ERRORLEVEL%
goto copy_notices

:use_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -m PyInstaller --version >nul 2>nul
if errorlevel 1 goto no_pyinstaller
python -m PyInstaller --noconfirm installer\pyinstaller\rubimorph.spec
if errorlevel 1 exit /b %ERRORLEVEL%
goto copy_notices

:copy_notices
if not exist LICENSE goto missing_license
if not exist THIRD_PARTY_NOTICES.md goto missing_third_party
copy /Y LICENSE dist\RubiMorph\LICENSE >nul
copy /Y THIRD_PARTY_NOTICES.md dist\RubiMorph\THIRD_PARTY_NOTICES.md >nul
if exist dist\RubiMorph\LICENSES rmdir /S /Q dist\RubiMorph\LICENSES
if exist dist\RubiMorph\docs rmdir /S /Q dist\RubiMorph\docs
if exist dist\RubiMorph\examples rmdir /S /Q dist\RubiMorph\examples
if exist dist\RubiMorph\schemas rmdir /S /Q dist\RubiMorph\schemas
xcopy LICENSES dist\RubiMorph\LICENSES /E /I /Y >nul
xcopy docs dist\RubiMorph\docs /E /I /Y >nul
xcopy examples dist\RubiMorph\examples /E /I /Y >nul
xcopy schemas dist\RubiMorph\schemas /E /I /Y >nul
goto verify_outputs

:verify_outputs
if not exist dist\RubiMorph\RubiMorph.exe goto missing_cli
if not exist dist\RubiMorph\RubiMorphGUI.exe goto missing_gui
if not exist dist\RubiMorph\_internal\python*.dll goto missing_python_dll
if not exist dist\RubiMorph\LICENSE goto missing_license_dist
if not exist dist\RubiMorph\THIRD_PARTY_NOTICES.md goto missing_third_party_dist
if not exist dist\RubiMorph\LICENSES\Python-3.14.3-LICENSE.txt goto missing_licenses_dist
if not exist dist\RubiMorph\docs\custom-format-profiles.md goto missing_docs_dist
if not exist dist\RubiMorph\examples\custom-profiles\example-bracket-format.rubimorph-profile.json goto missing_examples_dist
if not exist dist\RubiMorph\schemas\custom-format-profile-v1.schema.json goto missing_schemas_dist
exit /b 0

:missing_cli
echo dist\RubiMorph\RubiMorph.exe が見つかりません。
exit /b 1

:missing_gui
echo dist\RubiMorph\RubiMorphGUI.exe が見つかりません。
exit /b 1

:missing_python_dll
echo dist\RubiMorph\_internal\python*.dll が見つかりません。
exit /b 1

:missing_license
echo LICENSE が見つかりません。
exit /b 1

:missing_third_party
echo THIRD_PARTY_NOTICES.md が見つかりません。
exit /b 1

:missing_license_dist
echo dist\RubiMorph\LICENSE が見つかりません。
exit /b 1

:missing_third_party_dist
echo dist\RubiMorph\THIRD_PARTY_NOTICES.md が見つかりません。
exit /b 1

:missing_licenses_dist
echo dist\RubiMorph\LICENSES\Python-3.14.3-LICENSE.txt が見つかりません。
exit /b 1

:missing_docs_dist
echo dist\RubiMorph\docs\custom-format-profiles.md が見つかりません。
exit /b 1

:missing_examples_dist
echo dist\RubiMorph\examples\custom-profiles\example-bracket-format.rubimorph-profile.json が見つかりません。
exit /b 1

:missing_schemas_dist
echo dist\RubiMorph\schemas\custom-format-profile-v1.schema.json が見つかりません。
exit /b 1

:no_pyinstaller
echo PyInstaller が見つかりません。必要な場合は環境を確認してから導入し、再実行してください。
echo 例: py -3 -m pip install pyinstaller
exit /b 1

:no_python
echo Python が見つかりません。Python 3 をインストールしてから再実行してください。
exit /b 1
