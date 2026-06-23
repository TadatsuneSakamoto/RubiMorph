@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

echo build と dist は配布生成物です。削除する場合は内容を確認してから手動で削除してください。
echo このスクリプトは安全のため自動削除しません。
exit /b 0
