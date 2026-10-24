@echo off
cd /d "%~dp0.."
start "" /b powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0..\work\agent\projects_desk.ps1"
