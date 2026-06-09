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

echo Starting THC synchronization: all list queries except expedition details...
echo.
echo [1/3] Synchronizing catalogs...
python -u scripts\sync_catalogs.py --lang es_ES
if %errorlevel% neq 0 (
    echo Sync catalogs failed! Exiting.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Synchronizing all list queries except statistics_expeditions_details...
set FUNCTIONS=application_all catalog_items catalog_categories catalog_species catalog_reserves catalog_locations catalog_missions catalog_mission_groups catalog_collectables catalog_achievements catalog_ranks missions daily_missions_calendar user_by_hostname ranks_general ranks_animals ranks_weapons ranks_collectables achievements_general achievements_animals achievements_weapons achievements_exploration achievements_daily_missions achievements_challenges skills_species skills_weapons statistics_last_hunt statistics_lifetime statistics_history statistics_best gallery trophies dogs inventory friends competitions_upcoming competitions_previous competition_states community_league_states leaderboards_score leaderboards_range leaderboards_hunterscore leaderboards_hall_of_fame leaderboards_lanebandit leaderboards_bustthrough leaderboards_antlers_single leaderboards_antlers_double leaderboards_current_personal
set TOTAL=48
set COUNT=0

for %%F in (%FUNCTIONS%) do (
    set /a COUNT+=1
    echo.
    echo    [!COUNT!/%TOTAL%] %%F
    python -u scripts\sync_query_strict.py --user-id 29509787 --lang es_ES --oauth-access-token "%THC_OAUTH_ACCESS_TOKEN%" --function "%%F"
    if errorlevel 1 (
        echo Query sync failed or skipped for %%F! Exiting.
        pause
        exit /b 1
    )
)

echo.
echo [3/3] Recreating database views...
python -u scripts\apply_views.py
if %errorlevel% neq 0 (
    echo Applying views failed!
    pause
    exit /b %errorlevel%
)

echo.
echo Synchronization finished: all list queries except expedition details.
pause
exit /b 0
