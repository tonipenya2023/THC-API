@echo off
setlocal EnableExtensions EnableDelayedExpansion

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

echo Starting detailed THC synchronization...
echo.
echo [1/3] Synchronizing catalogs...
python -u scripts\sync_catalogs.py --lang es_ES
if %errorlevel% neq 0 (
    echo Sync catalogs failed! Exiting.
    if "%THC_SYNC_NO_PAUSE%"=="" pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Synchronizing queries one by one...
if "%THC_SYNC_FUNCTIONS%"=="" (
    set FUNCTIONS=application_all catalog_items catalog_categories catalog_species catalog_reserves catalog_locations catalog_missions catalog_mission_groups catalog_collectables catalog_achievements catalog_ranks missions daily_missions_calendar user_by_hostname ranks_general ranks_animals ranks_weapons ranks_collectables achievements_general achievements_animals achievements_weapons achievements_exploration achievements_daily_missions achievements_challenges skills_species skills_weapons statistics_last_hunt statistics_lifetime statistics_history statistics_expeditions_details statistics_best gallery trophies dogs inventory friends competitions_upcoming competitions_previous competition_states community_league_states competition_detail leaderboards_score leaderboards_range leaderboards_hunterscore leaderboards_hall_of_fame leaderboards_lanebandit leaderboards_bustthrough leaderboards_antlers_single leaderboards_antlers_double leaderboard_details_score leaderboard_details_range leaderboards_current_personal leaderboards_antler_detail
) else (
    set FUNCTIONS=%THC_SYNC_FUNCTIONS%
)
set TOTAL=0
for %%F in (%FUNCTIONS%) do (
    set /a TOTAL+=1
)
set COUNT=0
for %%F in (%FUNCTIONS%) do (
    set /a COUNT+=1
    echo.
    echo    [!COUNT!/%TOTAL%] %%F
    python -u scripts\sync_queries.py --user-id 29509787 --lang es_ES --oauth-access-token "%THC_OAUTH_ACCESS_TOKEN%" --function "%%F"
    if errorlevel 1 (
        echo Query sync failed for %%F! Exiting.
        if "%THC_SYNC_NO_PAUSE%"=="" pause
        exit /b 1
    )
)

echo.
echo [3/3] Recreating database views...
python -u scripts\apply_views.py
if %errorlevel% neq 0 (
    echo Applying views failed!
    if "%THC_SYNC_NO_PAUSE%"=="" pause
    exit /b %errorlevel%
)

echo.
echo Detailed synchronization finished.
if "%THC_SYNC_NO_PAUSE%"=="" pause
exit /b 0
