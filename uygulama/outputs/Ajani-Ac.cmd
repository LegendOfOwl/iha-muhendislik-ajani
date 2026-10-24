@echo off
setlocal
cd /d "%~dp0.."
set "ENGINEERING_CODEX=C:\Users\Urungu\AppData\Local\OpenAI\Codex\bin\9614f1d9b40d9c4f\codex.exe"
if not exist "%ENGINEERING_CODEX%" (
  echo Codex uygulamasi guncellenmis olabilir. Bu klasoru Codex uygulamasinda acin.
  pause
  exit /b 1
)
"%ENGINEERING_CODEX%" --search --sandbox workspace-write --ask-for-approval on-request
