@echo off
cd /d "%~dp0"
title Role Weaver Service
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-RoleWeaver.ps1" %*
if errorlevel 1 pause
