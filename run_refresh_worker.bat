@echo off
setlocal

cd /d "%~dp0"

set THC_DB_PASSWORD=system
set THC_DB_HOST=127.0.0.1
set THC_DB_PORT=5432
set THC_DB_NAME=thc_api
set THC_DB_USER=postgres

python -u scripts\refresh_worker.py
