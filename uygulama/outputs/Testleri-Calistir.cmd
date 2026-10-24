@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -X utf8 "work\tests\run_checks.py"
set "TEST_EXIT=%ERRORLEVEL%"
echo.
echo Rapor: outputs\reports\setup_report.md
echo Test cikis kodu: %TEST_EXIT%
pause
exit /b %TEST_EXIT%
