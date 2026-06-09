"""Reusable read-only client for theHunter Classic ranks API."""

from __future__ import annotations

import json
import time
from copy import deepcopy
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE = "https://api.thehunter.com"
API_V2_BASE = "https://apiv2.thehunter.com"
DEFAULT_TIMEOUT = 20
APPLICATION_CONSUMER_KEY = "441e726a14efb474b468bf646bc563d2bf520f20"
EXPEDITION_HISTORY_PAGE_SIZE = 50
DEFAULT_EXPEDITION_HISTORY_DAYS = 30
ACHIEVEMENT_ICON_BASE_URL = "https://static.thehunter.com/static/img/achievements"
ITEM_IMAGE_BASE_URL = "https://static.thehunter.com/static/img/items/256"
PAGED_REQUEST_SIZE = 100
_REQUEST_LOG: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "request_log", default=None
)


class ThcApiError(RuntimeError):
    """Raised when an upstream API request cannot be completed."""


def get_user_by_hostname(hostname: str) -> Any:
    return _request_json("/v1/Public_user/getByHostname", params={"hostname": hostname})


def _request_json(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    base_url: str = API_BASE,
    method: str = "GET",
) -> Any:
    encoded = urlencode(params or {})
    url = f"{base_url}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if encoded and method == "GET":
        url = f"{url}?{encoded}"
    elif method == "POST":
        data = encoded.encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"
    request = Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    request_log = _REQUEST_LOG.get()
    if request_log is not None:
        safe_params = {
            key: "<redacted>"
            if any(
                word in key.lower() for word in ("token", "password", "secret", "key")
            )
            else value
            for key, value in (params or {}).items()
        }
        copy_url = f"{base_url}{path}"
        if safe_params and method == "GET":
            copy_url = f"{copy_url}?{urlencode(safe_params)}"
        request_log.append(
            {
                "method": method,
                "url": f"{base_url}{path}",
                "params": safe_params,
                "copy_url": copy_url,
            }
        )

    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ThcApiError(f"Upstream HTTP {exc.code} for {path}") from exc
    except URLError as exc:
        raise ThcApiError(f"Upstream connection error for {path}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ThcApiError(f"Upstream returned invalid JSON for {path}") from exc


def _paged_request_json(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    list_key: str,
    total_key: str = "total",
    base_url: str = API_BASE,
    method: str = "GET",
    page_size: int = PAGED_REQUEST_SIZE,
    max_records: int | None = None,
) -> Any:
    offset = int((params or {}).get("offset", 0))
    merged: dict[str, Any] | None = None
    rows: list[Any] = []

    while True:
        page_params = dict(params or {})
        page_params["offset"] = offset
        page_params["limit"] = page_size
        page = _request_json(
            path,
            params=page_params,
            base_url=base_url,
            method=method,
        )

        if not isinstance(page, dict) or not isinstance(page.get(list_key), list):
            return page
        if merged is None:
            merged = {key: value for key, value in page.items() if key != list_key}

        page_rows = page[list_key]
        if max_records is None:
            rows.extend(page_rows)
        else:
            remaining = max_records - len(rows)
            if remaining > 0:
                rows.extend(page_rows[:remaining])
        total = page.get(total_key)
        try:
            total_count = int(total)
        except (TypeError, ValueError):
            total_count = None

        offset += len(page_rows)
        if max_records is not None and len(rows) >= max_records:
            break
        if not page_rows or (total_count is not None and offset >= total_count):
            break
        if len(page_rows) < page_size and total_count is None:
            break

    result = merged or {}
    result[list_key] = rows
    if total_key in result:
        result[f"{list_key}_count"] = len(rows)
    return result


@contextmanager
def capture_requests() -> Any:
    """Capture upstream request metadata while redacting credentials."""
    requests: list[dict[str, Any]] = []
    token = _REQUEST_LOG.set(requests)
    try:
        yield requests
    finally:
        _REQUEST_LOG.reset(token)


@lru_cache(maxsize=8)
def get_application_data(lang: str = "es_ES") -> dict[str, Any]:
    """Return the official localized static catalogs used by the web client."""
    return _request_json(
        "/v1/Application/application",
        params={"oauth_consumer_key": APPLICATION_CONSUMER_KEY, "lang": lang},
        method="POST",
    )


def get_application_catalog(catalog_name: str, lang: str = "es_ES") -> Any:
    """Return one official static catalog by name."""
    catalogs = get_application_data(lang)
    if catalog_name not in catalogs:
        raise ThcApiError(f"Unknown application catalog: {catalog_name}")
    return catalogs[catalog_name]


def get_catalog_items(lang: str = "es_ES") -> Any:
    return get_application_catalog("items", lang)


def get_catalog_categories(lang: str = "es_ES") -> Any:
    return get_application_catalog("categories", lang)


def get_catalog_species(lang: str = "es_ES") -> Any:
    return get_application_catalog("species", lang)


def get_catalog_reserves(lang: str = "es_ES") -> Any:
    return get_application_catalog("reserves", lang)


def get_catalog_locations(lang: str = "es_ES") -> Any:
    return get_application_catalog("locations", lang)


def get_catalog_missions(lang: str = "es_ES") -> Any:
    return get_application_catalog("missions", lang)


def get_catalog_mission_groups(lang: str = "es_ES") -> Any:
    return get_application_catalog("mission_groups", lang)


def get_catalog_collectables(lang: str = "es_ES") -> Any:
    return get_application_catalog("collectables", lang)


def get_catalog_achievements(lang: str = "es_ES") -> Any:
    return get_application_catalog("achievements", lang)


def get_catalog_ranks(lang: str = "es_ES") -> Any:
    return get_application_catalog("ranks", lang)


def get_missions(oauth_access_token: str) -> Any:
    return _request_json(
        "/v1/Mission/missions",
        params={"oauth_access_token": oauth_access_token},
        method="POST",
    )


def get_daily_missions_calendar(oauth_access_token: str) -> Any:
    return _request_json(
        "/v1/Daily_Mission/get_daily_missions_calendar",
        params={"oauth_access_token": oauth_access_token},
        method="POST",
    )


def get_ranks(user_id: int | str) -> list[dict[str, Any]]:
    """Return the complete ranks payload for one user."""
    return _request_json(f"/game/user/{int(user_id)}/ranks", base_url=API_V2_BASE)


def _filter_ranks(user_id: int | str, category_id: int) -> list[dict[str, Any]]:
    """Call the ranks API once and apply one local category filter."""
    return [item for item in get_ranks(user_id) if item.get("category_id") == category_id]


def get_ranks_general(user_id: int | str) -> list[dict[str, Any]]:
    return get_ranks(user_id)


def get_ranks_animals(user_id: int | str) -> list[dict[str, Any]]:
    return _filter_ranks(user_id, 1)


def get_ranks_weapons(user_id: int | str) -> list[dict[str, Any]]:
    return _filter_ranks(user_id, 2)


def get_ranks_collectables(user_id: int | str) -> list[dict[str, Any]]:
    return _filter_ranks(user_id, 3)


def get_achievements(user_id: int | str) -> list[dict[str, Any]]:
    """Return the complete achievements payload for one user."""
    return _request_json("/v1/Achievement/stats", params={"user_id": int(user_id)})


def _filter_achievements(
    user_id: int | str, category_id: int
) -> list[dict[str, Any]]:
    """Call the achievements API once and apply one local category filter."""
    return [
        item
        for item in get_achievements(user_id)
        if item.get("category_id") == category_id
    ]


def get_achievements_general(user_id: int | str) -> list[dict[str, Any]]:
    return get_achievements(user_id)


def get_achievements_animals(user_id: int | str) -> list[dict[str, Any]]:
    return _filter_achievements(user_id, 0)


def get_achievements_weapons(user_id: int | str) -> list[dict[str, Any]]:
    return _filter_achievements(user_id, 1)


def get_achievements_exploration(user_id: int | str) -> list[dict[str, Any]]:
    return _filter_achievements(user_id, 2)


def get_achievements_daily_missions(user_id: int | str) -> list[dict[str, Any]]:
    return _filter_achievements(user_id, 4)


def get_achievements_challenges(user_id: int | str, lang: str = "es_ES") -> Any:
    return {
        "definitions": _request_json(
            "/v1/Challenge/get_challenges", params={"lang": lang}
        ),
        "progress": _request_json(
            "/v1/Challenge/get_user_challenges",
            params={"user_id": int(user_id)},
        ),
    }


def get_skills(user_id: int | str) -> dict[str, Any]:
    """Return the complete skills payload for one user."""
    return _request_json("/v1/Skill/list", params={"user_id": int(user_id)})


def get_skills_species(user_id: int | str) -> Any:
    skills = get_skills(user_id)
    return {
        "tracking": skills.get("tracking", {}),
        "spotting": skills.get("spotting", {}),
    }


def get_skills_weapons(user_id: int | str) -> Any:
    return {"weapon": get_skills(user_id).get("weapon", {})}


def get_public_user_expedition(user_id: int | str, expedition_id: int | str) -> Any:
    """Return the full detail for one historical expedition, including all kills."""
    return _request_json(
        "/v1/Public_user/expedition",
        params={"user_id": int(user_id), "expedition_id": int(expedition_id)},
    )


def get_statistics_last_hunt(
    user_id: int | str, expedition_id: int | str | None = None
) -> Any:
    params = {"user_id": int(user_id)}
    if expedition_id is not None:
        params["expedition_id"] = int(expedition_id)
    return _request_json("/v1/Public_user/expedition", params=params)


def get_statistics_lifetime(user_id: int | str) -> Any:
    return _request_json("/v1/Statistics/total", params={"user_id": int(user_id)})


def _expedition_ts(expedition: dict[str, Any]) -> int | None:
    for key in ("start_ts", "end_ts"):
        value = expedition.get(key)
        if value in (None, ""):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _get_statistics_history_page(
    user_id: int | str, offset: int | str = 0, limit: int | str = 100
) -> Any:
    return _request_json(
        "/v1/Expedition/list",
        params={
            "user_id": int(user_id),
            "offset": int(offset),
            "limit": min(int(limit), EXPEDITION_HISTORY_PAGE_SIZE),
        },
    )


def get_statistics_history(
    user_id: int | str, days: int | str = DEFAULT_EXPEDITION_HISTORY_DAYS
) -> Any:
    day_window = int(days)
    if day_window <= 0:
        return {"total": 0, "days": day_window, "expeditions": []}

    cutoff_ts = int(time.time()) - day_window * 86400
    expeditions: list[dict[str, Any]] = []
    offset = 0
    result: dict[str, Any] = {}

    while True:
        history = _get_statistics_history_page(
            user_id=user_id,
            offset=offset,
            limit=EXPEDITION_HISTORY_PAGE_SIZE,
        )
        if isinstance(history, dict) and not result:
            result = {key: value for key, value in history.items() if key != "expeditions"}
        page = history.get("expeditions", []) if isinstance(history, dict) else []
        if not page:
            break

        recent = []
        reached_cutoff = False
        for expedition in page:
            if not isinstance(expedition, dict):
                continue
            expedition_ts = _expedition_ts(expedition)
            if expedition_ts is None or expedition_ts >= cutoff_ts:
                recent.append(expedition)
            else:
                reached_cutoff = True

        expeditions.extend(recent)
        if reached_cutoff:
            break
        offset += len(page)

    result["total"] = len(expeditions)
    result["days"] = day_window
    result["cutoff_ts"] = cutoff_ts
    result["expeditions"] = expeditions
    return result


def get_statistics_expeditions_details(
    user_id: int | str, days: int | str = DEFAULT_EXPEDITION_HISTORY_DAYS
) -> list[dict[str, Any]]:
    """Return full details for expeditions inside the recent day window.

    The history endpoint is read in pages until the requested date window is
    covered. For every selected expedition, /v1/Public_user/expedition is
    called with its expedition_id. The kills/animals inside each expedition are
    not limited here; the detail endpoint returns the full expedition payload.
    """
    history = get_statistics_history(user_id=user_id, days=days)
    expeditions = history.get("expeditions", []) if isinstance(history, dict) else []

    details = []
    for exp in expeditions:
        exp_id = exp.get("id")
        if not exp_id:
            continue
        try:
            details.append(
                get_public_user_expedition(user_id=user_id, expedition_id=exp_id)
            )
        except Exception:
            pass
    return details


def get_statistics_best(user_id: int | str, season_no: int | str = 0) -> Any:
    return _request_json(
        "/v1/Leaderboard/personal",
        params={"user_id": int(user_id), "season_no": int(season_no)},
    )


def get_gallery(
    user_id: int | str
) -> Any:
    return _paged_request_json(
        "/v1/Gallery/list",
        params={"user_id": int(user_id)},
        list_key="photos",
    )


def get_trophies(
    user_id: int | str
) -> Any:
    return _paged_request_json(
        "/v1/Trophy/list",
        params={"user_id": int(user_id)},
        list_key="trophies",
    )


def get_dogs(user_id: int | str) -> Any:
    return _request_json(
        "/v1/Inventory/dict", params={"user_id": int(user_id), "category_id": 12}
    )


def get_inventory(user_id: int | str) -> list[dict[str, Any]]:
    """Return one valued row per owned item type."""
    inventory = _request_json("/v1/Inventory/list", params={"user_id": int(user_id)})
    rows: list[dict[str, Any]] = []
    for inventory_item in inventory:
        item = inventory_item.get("item", {})
        subcategory = item.get("subcat") or {}
        own = inventory_item.get("own", [])
        item_units = item.get("units") or {}
        package_units = item_units.get("count", 1) or 1
        units = sum(
            instance.get("units", 0) or 1
            for instance in own
            if isinstance(instance.get("units"), (int, float))
        )
        price = item.get("price")
        silver_price = item.get("silver_price")
        rows.append(
            {
                "item_id": item.get("id"),
                "name": item.get("name"),
                "variationname": item.get("variationname"),
                "category_id": item.get("cat"),
                "subcategory_id": subcategory.get("id"),
                "owned_instances": len(own),
                "units": units,
                "price": price,
                "silver_price": silver_price,
                "valorem": units * price / package_units
                if isinstance(price, (int, float))
                else None,
                "valorgm": units * silver_price / package_units
                if isinstance(silver_price, (int, float))
                else None,
            }
        )
    rows.append(
        {
            "item_id": None,
            "name": "TOTAL INVENTORY",
            "variationname": None,
            "category_id": None,
            "subcategory_id": None,
            "owned_instances": sum(row["owned_instances"] for row in rows),
            "units": sum(row["units"] for row in rows),
            "price": None,
            "silver_price": None,
            "valorem": sum(row["valorem"] or 0 for row in rows),
            "valorgm": sum(row["valorgm"] or 0 for row in rows),
        }
    )
    return rows


def get_friends(
    user_id: int | str
) -> Any:
    return _paged_request_json(
        "/v1/User/friendslist",
        params={"user_id": int(user_id)},
        list_key="friends",
    )


def get_competitions_upcoming(lang: str = "es_ES") -> Any:
    return _request_json("/v1/Page_content/list_competitions", params={"lang": lang})


def get_competitions_previous(
    lang: str = "es_ES", max_records: int | None = None
) -> Any:
    return _paged_request_json(
        "/v1/Page_content/list_previous_competitions",
        params={"lang": lang},
        list_key="competitions",
        max_records=max_records,
    )


def get_competition_states(oauth_access_token: str) -> Any:
    return _request_json(
        "/v1/Page_content/competition_states",
        params={"oauth_access_token": oauth_access_token},
        method="POST",
    )


def get_community_league_states(oauth_access_token: str) -> Any:
    return _request_json(
        "/v1/Page_content/competition_community_league_states",
        params={"oauth_access_token": oauth_access_token},
        method="POST",
    )


def get_competition_detail(
    competition_id: int | str, lang: str = "es_ES"
) -> Any:
    return _request_json(
        "/v1/Page_content/competitions_new",
        params={
            "id": int(competition_id),
            "lang": lang,
        },
    )


def _get_leaderboards(leaderboard_type: int) -> Any:
    return _request_json(
        "/v1/Page_content/leaderboards_all",
        params={"type": leaderboard_type},
        method="POST",
    )


def _records_from_leaderboard_detail(value: Any) -> list[Any] | None:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return None
    for key in ("records", "entries", "positions", "leaderboard", "data"):
        item = value.get(key)
        if isinstance(item, list):
            return item
    return None


def _leaderboard_id(value: dict[str, Any]) -> Any:
    for key in ("id", "species", "species_id", "animal_id"):
        if value.get(key) not in (None, ""):
            return value[key]
    return None


def _get_leaderboards_with_details(leaderboard_type: int) -> Any:
    summaries = _get_leaderboards(leaderboard_type)
    if not isinstance(summaries, list):
        return summaries
    detailed: list[Any] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            detailed.append(summary)
            continue
        species_id = _leaderboard_id(summary)
        if species_id is None:
            detailed.append(summary)
            continue
        entry = dict(summary)
        try:
            detail = _get_leaderboard_details(leaderboard_type, species_id)
        except ThcApiError:
            detailed.append(entry)
            continue
        records = _records_from_leaderboard_detail(detail)
        if records is not None:
            entry["records"] = records
        elif isinstance(detail, dict):
            for key, value in detail.items():
                if key not in entry or key == "records":
                    entry[key] = value
        detailed.append(entry)
    return detailed


def get_leaderboards_score() -> Any:
    return _get_leaderboards_with_details(1)


def get_leaderboards_range() -> Any:
    return _get_leaderboards_with_details(2)


def get_leaderboards_hunterscore(max_records: int | None = None) -> Any:
    return _paged_request_json(
        "/v1/Page_content/hunterscores",
        params={},
        list_key="records",
        max_records=max_records,
    )


def get_leaderboards_hall_of_fame(season_no: int | str) -> Any:
    return _request_json(
        "/v1/Page_content/leaderboards_hall_of_fame",
        params={"season_no": int(season_no)},
    )


def _get_leaderboards_minigame(
    game_id: int, user_id: int | str, max_records: int | None = None
) -> Any:
    return _paged_request_json(
        "/v1/Page_content/minigames_list",
        params={
            "game_id": game_id,
            "user_id": int(user_id),
        },
        list_key="records",
        max_records=max_records,
    )


def get_leaderboards_lanebandit(
    user_id: int | str, max_records: int | None = None
) -> Any:
    return _get_leaderboards_minigame(1, user_id, max_records=max_records)


def get_leaderboards_bustthrough(
    user_id: int | str, max_records: int | None = None
) -> Any:
    return _get_leaderboards_minigame(0, user_id, max_records=max_records)


def _get_leaderboards_antlers(antler_type: str) -> Any:
    return _request_json(
        f"/game/user/leaderboards/antlers/{antler_type}/all",
        base_url=API_V2_BASE,
    )


def get_leaderboards_antlers_single() -> Any:
    return _get_leaderboards_antlers("single")


def get_leaderboards_antlers_double() -> Any:
    return _get_leaderboards_antlers("double")


def _get_leaderboard_details(leaderboard_type: int, species_id: int | str) -> Any:
    return _request_json(
        "/v1/Page_content/leaderboard_details",
        params={"type": leaderboard_type, "species": int(species_id)},
    )


def get_leaderboard_details_score(species_id: int | str) -> Any:
    return _get_leaderboard_details(1, species_id)


def get_leaderboard_details_range(species_id: int | str) -> Any:
    return _get_leaderboard_details(2, species_id)


def get_leaderboards_current_personal(user_id: int | str) -> Any:
    return _request_json(
        "/v1/Leaderboard/current_personal",
        params={"user_id": int(user_id)},
        method="POST",
    )


def get_leaderboards_antler_detail(antler_type: str, antler_id: int | str) -> Any:
    return _request_json(
        f"/game/user/leaderboards/antlers/{antler_type}/{int(antler_id)}",
        base_url=API_V2_BASE,
    )


@lru_cache(maxsize=8)
def _catalog_indexes(lang: str) -> dict[str, dict[str, dict[str, Any]]]:
    catalogs = get_application_data(lang)
    names = (
        "items",
        "species",
        "reserves",
        "locations",
        "missions",
        "mission_groups",
        "collectables",
        "achievements",
    )
    indexes: dict[str, dict[str, dict[str, Any]]] = {}
    for name in names:
        values = catalogs.get(name, [])
        if isinstance(values, dict):
            values = values.values()
        indexes[name] = {
            str(value["id"]): value
            for value in values
            if isinstance(value, dict) and "id" in value
        }
    return indexes


def _reference(indexes: dict[str, Any], catalog: str, value: Any) -> Any:
    if isinstance(value, list):
        return [
            resolved
            for item in value
            if (resolved := _reference(indexes, catalog, item)) is not None
        ]
    if isinstance(value, (dict, list)) or value is None:
        return None
    resolved = indexes.get(catalog, {}).get(str(value))
    return _with_visual_metadata(catalog, resolved) if resolved is not None else None


def _with_visual_metadata(catalog: str, value: dict[str, Any]) -> dict[str, Any]:
    enriched = deepcopy(value)
    if catalog == "achievements" and isinstance(enriched.get("icon_url"), str):
        icon_path = enriched["icon_url"].lstrip("/")
        enriched["icon_url_absolute"] = f"{ACHIEVEMENT_ICON_BASE_URL}/{icon_path}"
    if catalog == "items" and isinstance(enriched.get("image"), str):
        image_key = enriched["image"].strip().lstrip("/")
        enriched["image_key"] = image_key
        enriched["image_url_absolute"] = f"{ITEM_IMAGE_BASE_URL}/{image_key}.png"
    return enriched


def _add_catalog_visuals(catalog: str, value: Any) -> Any:
    if isinstance(value, list):
        return [
            _with_visual_metadata(catalog, item) if isinstance(item, dict) else item
            for item in value
        ]
    if isinstance(value, dict):
        return _with_visual_metadata(catalog, value)
    return value


def _enrich_known_references(value: Any, indexes: dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [_enrich_known_references(item, indexes) for item in value]
    if not isinstance(value, dict):
        return value

    enriched = {
        key: _enrich_known_references(item, indexes) for key, item in value.items()
    }
    rules = {
        "species": "species",
        "species_id": "species",
        "weapon_id": "items",
        "ammo_id": "items",
        "item_id": "items",
        "reserve": "reserves",
        "reserve_id": "reserves",
        "location_id": "locations",
        "collectable_id": "collectables",
        "achievement_id": "achievements",
        "mission_id": "missions",
        "weapons": "items",
        "reserves": "reserves",
        "dependencies": "missions",
    }
    for key, catalog in rules.items():
        if key in value:
            resolved = _reference(indexes, catalog, value[key])
            if resolved is not None:
                enriched[f"{key}_resolved"] = resolved
    return enriched


def _resolve_entry_ids(value: Any, indexes: dict[str, Any], catalog: str) -> Any:
    if not isinstance(value, list):
        return value
    enriched = []
    for item in value:
        if not isinstance(item, dict):
            enriched.append(item)
            continue
        entry = dict(item)
        resolved = _reference(indexes, catalog, item.get("id"))
        if resolved is not None:
            entry["id_resolved"] = resolved
        enriched.append(entry)
    return enriched


def _resolve_dict_keys(value: Any, indexes: dict[str, Any], catalog: str) -> Any:
    if not isinstance(value, dict):
        return value
    enriched = dict(value)
    enriched["_resolved_keys"] = [
        {
            "id": key,
            "id_resolved": resolved,
            "value": item,
        }
        for key, item in value.items()
        if (resolved := _reference(indexes, catalog, key)) is not None
    ]
    return enriched


def _resolve_mission_state(value: Any, indexes: dict[str, Any]) -> Any:
    if not isinstance(value, dict):
        return value
    enriched = dict(value)
    for key in ("available", "active", "completed", "favourites"):
        if key in value:
            enriched[f"{key}_resolved"] = _reference(indexes, "missions", value[key])
    if isinstance(value.get("states"), dict):
        enriched["states_resolved"] = [
            {
                "mission_id": mission_id,
                "mission": _reference(indexes, "missions", mission_id),
                "state": state,
            }
            for mission_id, state in value["states"].items()
        ]
    return enriched


def enrich_response(function_name: str, value: Any, lang: str = "es_ES") -> Any:
    """Add known catalog references while preserving every original ID."""
    if function_name == "application_all":
        enriched = deepcopy(value)
        if isinstance(enriched, dict):
            for catalog in ("achievements", "items"):
                if catalog in enriched:
                    enriched[catalog] = _add_catalog_visuals(catalog, enriched[catalog])
        return enriched
    if function_name == "catalog_achievements":
        return _add_catalog_visuals("achievements", value)
    if function_name == "catalog_items":
        return _add_catalog_visuals("items", value)
    if function_name == "inventory" or function_name.startswith("catalog_"):
        return deepcopy(value)

    indexes = _catalog_indexes(lang)
    enriched = _enrich_known_references(deepcopy(value), indexes)

    if function_name in {"leaderboards_score", "leaderboards_range"}:
        return _resolve_entry_ids(enriched, indexes, "species")
    if function_name == "achievements_challenges" and isinstance(enriched, dict):
        enriched["definitions"] = _add_catalog_visuals(
            "achievements", enriched.get("definitions")
        )
        return enriched
    if function_name == "dogs":
        return _resolve_dict_keys(enriched, indexes, "items")
    if function_name == "skills_species" and isinstance(enriched, dict):
        for key in ("tracking", "spotting"):
            enriched[key] = _resolve_dict_keys(enriched.get(key), indexes, "species")
    if function_name == "skills_weapons" and isinstance(enriched, dict):
        enriched["weapon"] = _resolve_dict_keys(enriched.get("weapon"), indexes, "items")
    if function_name == "missions":
        return _resolve_mission_state(enriched, indexes)
    return enriched


from .thc_client_registry import build_functions


FUNCTIONS = build_functions(globals())


def list_functions() -> list[dict[str, Any]]:
    """Return frontend-safe metadata for the available reusable functions."""
    return [
        {
            "name": name,
            "label": item["label"],
            "group": item["group"],
            "params": item["params"],
        }
        for name, item in FUNCTIONS.items()
    ]


def call_function(
    name: str, params: dict[str, Any] | None = None, *, enrich_ids: bool = False
) -> Any:
    """Execute one registered function with validated frontend parameters."""
    if name not in FUNCTIONS:
        raise ThcApiError(f"Unknown function: {name}")

    supplied = params or {}
    kwargs: dict[str, Any] = {}

    for spec in FUNCTIONS[name]["params"]:
        value = supplied.get(spec["name"], spec["default"])
        if value == "":
            raise ThcApiError(f"{spec['label']} is required")
        if spec["type"] == "number":
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                raise ThcApiError(f"{spec['label']} must be an integer") from exc
        kwargs[spec["name"]] = value

    result = FUNCTIONS[name]["callback"](**kwargs)
    if enrich_ids:
        return enrich_response(name, result, str(supplied.get("lang", "es_ES")))
    return result


def call_function_with_requests(
    name: str, params: dict[str, Any] | None = None, *, enrich_ids: bool = False
) -> dict[str, Any]:
    """Execute one function and return its data plus safe upstream request metadata."""
    with capture_requests() as requests:
        result = call_function(name, params, enrich_ids=enrich_ids)
    return {"data": result, "requests": requests}
