@echo off
setlocal

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

echo Starting full THC synchronization...
echo.
echo [1/3] Synchronizing catalogs...
python scripts\sync_catalogs.py --lang es_ES
if %errorlevel% neq 0 (
    echo Sync catalogs failed! Exiting.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Synchronizing all queries...
python scripts\sync_queries.py --user-id 29509787 --lang es_ES --oauth-access-token "%THC_OAUTH_ACCESS_TOKEN%"
if %errorlevel% neq 0 (
    echo Sync queries failed! Exiting.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Recreating database views...
python scripts\apply_views.py
if %errorlevel% neq 0 (
    echo Applying views failed!
    pause
    exit /b %errorlevel%
)
echo.
echo Full synchronization finished.
pause
