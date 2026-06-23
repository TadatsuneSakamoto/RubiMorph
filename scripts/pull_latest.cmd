@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

git fetch origin
if errorlevel 1 exit /b %ERRORLEVEL%
git pull --ff-only origin main
exit /b %ERRORLEVEL%
