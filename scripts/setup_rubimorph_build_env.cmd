@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup_rubimorph_build_env.ps1" %*
exit /b %ERRORLEVEL%
