@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

if not exist dist (
  echo dist フォルダがありません。先に配布物を作成してください。
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path 'dist' -File -Recurse | Where-Object { $_.Name -ne 'SHA256SUMS.txt' } | ForEach-Object { $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName; '{0}  {1}' -f $hash.Hash.ToLowerInvariant(), ($_.FullName.Substring((Resolve-Path 'dist').Path.Length + 1) -replace '\\','/') } | Set-Content -LiteralPath 'dist\SHA256SUMS.txt' -Encoding UTF8"
exit /b %ERRORLEVEL%
