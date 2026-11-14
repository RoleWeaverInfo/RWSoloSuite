@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Adventure.ps1" -ChooseMode %*
if errorlevel 1 pause
