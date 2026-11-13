@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-SoloStudio.ps1" -Player
if errorlevel 1 pause
