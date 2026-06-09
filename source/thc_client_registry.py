"""Frontend function registry for the reusable THC client."""

from __future__ import annotations

from typing import Any, Callable


def _param(
    name: str, label: str, default: Any, kind: str = "number"
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "type": kind,
        "default": default,
        "required": True,
    }


def _entry(
    label: str,
    callback: Callable[..., Any],
    params: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "label": label,
        "group": "Ranks",
        "callback": callback,
        "params": params,
    }




def build_functions(callbacks: dict[str, Callable[..., Any]]) -> dict[str, dict[str, Any]]:
    get_achievements_animals = callbacks["get_achievements_animals"]
    get_achievements_challenges = callbacks["get_achievements_challenges"]
    get_achievements_daily_missions = callbacks["get_achievements_daily_missions"]
    get_achievements_exploration = callbacks["get_achievements_exploration"]
    get_achievements_general = callbacks["get_achievements_general"]
    get_achievements_weapons = callbacks["get_achievements_weapons"]
    get_application_data = callbacks["get_application_data"]
    get_catalog_achievements = callbacks["get_catalog_achievements"]
    get_catalog_categories = callbacks["get_catalog_categories"]
    get_catalog_collectables = callbacks["get_catalog_collectables"]
    get_catalog_items = callbacks["get_catalog_items"]
    get_catalog_locations = callbacks["get_catalog_locations"]
    get_catalog_mission_groups = callbacks["get_catalog_mission_groups"]
    get_catalog_missions = callbacks["get_catalog_missions"]
    get_catalog_ranks = callbacks["get_catalog_ranks"]
    get_catalog_reserves = callbacks["get_catalog_reserves"]
    get_catalog_species = callbacks["get_catalog_species"]
    get_community_league_states = callbacks["get_community_league_states"]
    get_competition_detail = callbacks["get_competition_detail"]
    get_competition_states = callbacks["get_competition_states"]
    get_competitions_previous = callbacks["get_competitions_previous"]
    get_competitions_upcoming = callbacks["get_competitions_upcoming"]
    get_daily_missions_calendar = callbacks["get_daily_missions_calendar"]
    get_dogs = callbacks["get_dogs"]
    get_friends = callbacks["get_friends"]
    get_gallery = callbacks["get_gallery"]
    get_inventory = callbacks["get_inventory"]
    get_leaderboard_details_range = callbacks["get_leaderboard_details_range"]
    get_leaderboard_details_score = callbacks["get_leaderboard_details_score"]
    get_leaderboards_antler_detail = callbacks["get_leaderboards_antler_detail"]
    get_leaderboards_antlers_double = callbacks["get_leaderboards_antlers_double"]
    get_leaderboards_antlers_single = callbacks["get_leaderboards_antlers_single"]
    get_leaderboards_bustthrough = callbacks["get_leaderboards_bustthrough"]
    get_leaderboards_current_personal = callbacks["get_leaderboards_current_personal"]
    get_leaderboards_hall_of_fame = callbacks["get_leaderboards_hall_of_fame"]
    get_leaderboards_hunterscore = callbacks["get_leaderboards_hunterscore"]
    get_leaderboards_lanebandit = callbacks["get_leaderboards_lanebandit"]
    get_leaderboards_range = callbacks["get_leaderboards_range"]
    get_leaderboards_score = callbacks["get_leaderboards_score"]
    get_missions = callbacks["get_missions"]
    get_ranks_animals = callbacks["get_ranks_animals"]
    get_ranks_collectables = callbacks["get_ranks_collectables"]
    get_ranks_general = callbacks["get_ranks_general"]
    get_ranks_weapons = callbacks["get_ranks_weapons"]
    get_skills_species = callbacks["get_skills_species"]
    get_skills_weapons = callbacks["get_skills_weapons"]
    get_statistics_best = callbacks["get_statistics_best"]
    get_statistics_expeditions_details = callbacks["get_statistics_expeditions_details"]
    get_statistics_history = callbacks["get_statistics_history"]
    get_statistics_last_hunt = callbacks["get_statistics_last_hunt"]
    get_statistics_lifetime = callbacks["get_statistics_lifetime"]
    get_trophies = callbacks["get_trophies"]
    get_user_by_hostname = callbacks["get_user_by_hostname"]

    USER_ID = _param("user_id", "User ID", 29509787)
    LANG = _param("lang", "Language", "es_ES", "text")
    TOKEN = _param("oauth_access_token", "OAuth access token", "", "password")


    FUNCTIONS = {
        "application_all": {
            "label": "Catalogs - all application data",
            "group": "Catalogs",
            "callback": get_application_data,
            "params": [LANG],
        },
        "catalog_items": {
            "label": "Catalogs - items",
            "group": "Catalogs",
            "callback": get_catalog_items,
            "params": [LANG],
        },
        "catalog_categories": {
            "label": "Catalogs - item categories",
            "group": "Catalogs",
            "callback": get_catalog_categories,
            "params": [LANG],
        },
        "catalog_species": {
            "label": "Catalogs - species",
            "group": "Catalogs",
            "callback": get_catalog_species,
            "params": [LANG],
        },
        "catalog_reserves": {
            "label": "Catalogs - reserves",
            "group": "Catalogs",
            "callback": get_catalog_reserves,
            "params": [LANG],
        },
        "catalog_locations": {
            "label": "Catalogs - locations",
            "group": "Catalogs",
            "callback": get_catalog_locations,
            "params": [LANG],
        },
        "catalog_missions": {
            "label": "Catalogs - missions",
            "group": "Catalogs",
            "callback": get_catalog_missions,
            "params": [LANG],
        },
        "catalog_mission_groups": {
            "label": "Catalogs - mission groups",
            "group": "Catalogs",
            "callback": get_catalog_mission_groups,
            "params": [LANG],
        },
        "catalog_collectables": {
            "label": "Catalogs - collectables",
            "group": "Catalogs",
            "callback": get_catalog_collectables,
            "params": [LANG],
        },
        "catalog_achievements": {
            "label": "Catalogs - achievements",
            "group": "Catalogs",
            "callback": get_catalog_achievements,
            "params": [LANG],
        },
        "catalog_ranks": {
            "label": "Catalogs - ranks",
            "group": "Catalogs",
            "callback": get_catalog_ranks,
            "params": [LANG],
        },
        "missions": {
            "label": "Missions - personal state",
            "group": "Missions",
            "callback": get_missions,
            "params": [TOKEN],
        },
        "daily_missions_calendar": {
            "label": "Missions - daily calendar",
            "group": "Missions",
            "callback": get_daily_missions_calendar,
            "params": [TOKEN],
        },
        "user_by_hostname": {
            "label": "User by hostname",
            "group": "Profile",
            "callback": get_user_by_hostname,
            "params": [_param("hostname", "Hostname", "nefastix13", "text")],
        },
        "ranks_general": _entry("Ranks - general", get_ranks_general, [USER_ID]),
        "ranks_animals": _entry("Ranks - animals", get_ranks_animals, [USER_ID]),
        "ranks_weapons": _entry("Ranks - weapons", get_ranks_weapons, [USER_ID]),
        "ranks_collectables": _entry(
            "Ranks - collectables", get_ranks_collectables, [USER_ID]
        ),
        "achievements_general": {
            "label": "Achievements - general",
            "group": "Achievements",
            "callback": get_achievements_general,
            "params": [USER_ID],
        },
        "achievements_animals": {
            "label": "Achievements - animals",
            "group": "Achievements",
            "callback": get_achievements_animals,
            "params": [USER_ID],
        },
        "achievements_weapons": {
            "label": "Achievements - weapons",
            "group": "Achievements",
            "callback": get_achievements_weapons,
            "params": [USER_ID],
        },
        "achievements_exploration": {
            "label": "Achievements - exploration",
            "group": "Achievements",
            "callback": get_achievements_exploration,
            "params": [USER_ID],
        },
        "achievements_daily_missions": {
            "label": "Achievements - daily missions",
            "group": "Achievements",
            "callback": get_achievements_daily_missions,
            "params": [USER_ID],
        },
        "achievements_challenges": {
            "label": "Achievements - challenges",
            "group": "Achievements",
            "callback": get_achievements_challenges,
            "params": [USER_ID, LANG],
        },
        "skills_species": {
            "label": "Skills - species",
            "group": "Skills",
            "callback": get_skills_species,
            "params": [USER_ID],
        },
        "skills_weapons": {
            "label": "Skills - weapons",
            "group": "Skills",
            "callback": get_skills_weapons,
            "params": [USER_ID],
        },
        "statistics_last_hunt": {
            "label": "Statistics - last hunt",
            "group": "Statistics",
            "callback": get_statistics_last_hunt,
            "params": [USER_ID],
        },
        "statistics_lifetime": {
            "label": "Statistics - lifetime",
            "group": "Statistics",
            "callback": get_statistics_lifetime,
            "params": [USER_ID],
        },
        "statistics_history": {
            "label": "Statistics - history",
            "group": "Statistics",
            "callback": get_statistics_history,
            "params": [USER_ID, _param("days", "Days", 30)],
        },
        "statistics_expeditions_details": {
            "label": "Statistics - expeditions details",
            "group": "Statistics",
            "callback": get_statistics_expeditions_details,
            "params": [USER_ID, _param("days", "Days", 30)],
        },
        "statistics_best": {
            "label": "Statistics - personal bests",
            "group": "Statistics",
            "callback": get_statistics_best,
            "params": [USER_ID, _param("season_no", "Season", 0)],
        },
        "gallery": {
            "label": "Gallery",
            "group": "Profile",
            "callback": get_gallery,
            "params": [USER_ID],
        },
        "trophies": {
            "label": "Trophies",
            "group": "Profile",
            "callback": get_trophies,
            "params": [USER_ID],
        },
        "dogs": {
            "label": "Dogs",
            "group": "Profile",
            "callback": get_dogs,
            "params": [USER_ID],
        },
        "inventory": {
            "label": "Inventory - valued lines",
            "group": "Profile",
            "callback": get_inventory,
            "params": [USER_ID],
        },
        "friends": {
            "label": "Friends",
            "group": "Profile",
            "callback": get_friends,
            "params": [USER_ID],
        },
        "competitions_upcoming": {
            "label": "Competitions - upcoming",
            "group": "Competitions",
            "callback": get_competitions_upcoming,
            "params": [LANG],
        },
        "competitions_previous": {
            "label": "Competitions - previous",
            "group": "Competitions",
            "callback": get_competitions_previous,
            "params": [LANG],
        },
        "competition_states": {
            "label": "Competitions - personal states",
            "group": "Competitions",
            "callback": get_competition_states,
            "params": [TOKEN],
        },
        "community_league_states": {
            "label": "Community league - personal states",
            "group": "Competitions",
            "callback": get_community_league_states,
            "params": [TOKEN],
        },
        "competition_detail": {
            "label": "Competition - detail",
            "group": "Competitions",
            "callback": get_competition_detail,
            "params": [
                _param("competition_id", "Competition ID", 173939),
                LANG,
            ],
        },
        "leaderboards_score": {
            "label": "Leaderboards - score",
            "group": "Leaderboards",
            "callback": get_leaderboards_score,
            "params": [],
        },
        "leaderboards_range": {
            "label": "Leaderboards - range",
            "group": "Leaderboards",
            "callback": get_leaderboards_range,
            "params": [],
        },
        "leaderboards_hunterscore": {
            "label": "Leaderboards - hunterscore",
            "group": "Leaderboards",
            "callback": get_leaderboards_hunterscore,
            "params": [],
        },
        "leaderboards_hall_of_fame": {
            "label": "Leaderboards - hall of fame",
            "group": "Leaderboards",
            "callback": get_leaderboards_hall_of_fame,
            "params": [_param("season_no", "Season", 39)],
        },
        "leaderboards_lanebandit": {
            "label": "Leaderboards - lanebandit",
            "group": "Leaderboards",
            "callback": get_leaderboards_lanebandit,
            "params": [USER_ID],
        },
        "leaderboards_bustthrough": {
            "label": "Leaderboards - bustthrough",
            "group": "Leaderboards",
            "callback": get_leaderboards_bustthrough,
            "params": [USER_ID],
        },
        "leaderboards_antlers_single": {
            "label": "Leaderboards - antlers single",
            "group": "Leaderboards",
            "callback": get_leaderboards_antlers_single,
            "params": [],
        },
        "leaderboards_antlers_double": {
            "label": "Leaderboards - antlers double",
            "group": "Leaderboards",
            "callback": get_leaderboards_antlers_double,
            "params": [],
        },
        "leaderboard_details_score": {
            "label": "Leaderboard detail - score",
            "group": "Leaderboards",
            "callback": get_leaderboard_details_score,
            "params": [_param("species_id", "Species ID", 0)],
        },
        "leaderboard_details_range": {
            "label": "Leaderboard detail - range",
            "group": "Leaderboards",
            "callback": get_leaderboard_details_range,
            "params": [_param("species_id", "Species ID", 0)],
        },
        "leaderboards_current_personal": {
            "label": "Leaderboards - current personal",
            "group": "Leaderboards",
            "callback": get_leaderboards_current_personal,
            "params": [USER_ID],
        },
        "leaderboards_antler_detail": {
            "label": "Leaderboard detail - antler",
            "group": "Leaderboards",
            "callback": get_leaderboards_antler_detail,
            "params": [
                _param("antler_type", "Antler type", "single", "text"),
                _param("antler_id", "Antler ID", 2006),
            ],
        },
    }
    return FUNCTIONS
