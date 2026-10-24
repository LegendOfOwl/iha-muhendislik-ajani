@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -X utf8 "work\engineering\evaluate_inputs.py"
set "CHECK_EXIT=%ERRORLEVEL%"
echo.
echo Rapor: outputs\reports\input_check.json
echo 0: kosullu kaldirma hesabi; 2: eksik veya gecersiz girdi, sayisal sonuc yok.
pause
exit /b %CHECK_EXIT%
