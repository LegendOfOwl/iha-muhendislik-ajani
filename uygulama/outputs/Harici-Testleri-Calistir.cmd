@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -X utf8 "work\native\run_all.py"
set "RUN_EXIT=%ERRORLEVEL%"
echo.
echo Rapor: outputs\reports\external_tools_report.md
echo Cikis kodu: %RUN_EXIT%
pause
exit /b %RUN_EXIT%
