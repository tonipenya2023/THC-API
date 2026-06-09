@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set THC_DB_PASSWORD=system
set THC_DB_HOST=127.0.0.1
set THC_DB_PORT=5432
set THC_DB_NAME=thc_api
set THC_DB_USER=postgres
set THC_OAUTH_ACCESS_TOKEN=39be3a3648298915c1a3d62edead770c

if not "%~1"=="" (
    set THC_OAUTH_ACCESS_TOKEN=%~1
)

echo Starting timed THC query synchronization...
echo.
python -u scripts\sync_queries_timed.py --user-id 29509787 --lang es_ES --oauth-access-token "%THC_OAUTH_ACCESS_TOKEN%"
if %errorlevel% neq 0 (
    echo Timed synchronization finished with errors or skipped functions.
    pause
    exit /b %errorlevel%
)

echo.
echo Recreating database views...
python -u scripts\apply_views.py
if %errorlevel% neq 0 (
    echo Applying views failed!
    pause
    exit /b %errorlevel%
)

echo.
echo Timed synchronization finished.
pause
exit /b 0
