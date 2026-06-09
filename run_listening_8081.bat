@echo off
setlocal

cd /d "%~dp0"
set THC_API_PORT=8081

py "%~dp0thc_api.py"
