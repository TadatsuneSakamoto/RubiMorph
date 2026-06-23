@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m unittest discover -s tests -v
exit /b %ERRORLEVEL%

:use_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -m unittest discover -s tests -v
exit /b %ERRORLEVEL%

:no_python
echo Python が見つかりません。Python 3 をインストールしてから再実行してください。
exit /b 1
