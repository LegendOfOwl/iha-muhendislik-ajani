@echo off
setlocal
cd /d "%~dp0.."
start "OpenVSP" "tools\openvsp\OpenVSP-3.55.0-win64\vsp.exe" "outputs\cad\aircraft_demo.vsp3"
