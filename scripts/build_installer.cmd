@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

if not exist dist\RubiMorph\RubiMorph.exe goto no_exe
if not exist dist\RubiMorph\RubiMorphGUI.exe goto no_gui_exe
if not exist dist\RubiMorph\_internal\python*.dll goto no_python_dll
if not exist VERSION goto no_version

set /p RUBIMORPH_VERSION=<VERSION
if "%RUBIMORPH_VERSION%"=="" goto no_version

set "ISCC_EXE=iscc"
where iscc >nul 2>nul
if not errorlevel 1 goto run_iscc

if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"

if "%ISCC_EXE%"=="iscc" goto no_inno

:run_iscc
"%ISCC_EXE%" "/DMyAppVersion=%RUBIMORPH_VERSION%" installer\inno\rubimorph.iss
exit /b %ERRORLEVEL%

:no_version
echo VERSION が見つからないか空です。
exit /b 1

:no_exe
echo dist\RubiMorph\RubiMorph.exe が見つかりません。
echo 先に scripts\build_exe.cmd を実行してください。
exit /b 1

:no_gui_exe
echo dist\RubiMorph\RubiMorphGUI.exe が見つかりません。
echo 先に scripts\build_exe.cmd を実行してください。
exit /b 1

:no_python_dll
echo dist\RubiMorph\_internal\python*.dll が見つかりません。
echo dist\RubiMorph 配下全体を再生成するため、先に scripts\build_exe.cmd を実行してください。
exit /b 1

:no_inno
echo Inno Setup Compiler の iscc が見つかりません。
echo installer\inno\rubimorph.iss を使う場合は Inno Setup を導入し、iscc に PATH を通してください。
exit /b 1
