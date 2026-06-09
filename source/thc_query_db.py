"""Generic PostgreSQL persistence for reusable theHunter API queries."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from psycopg2 import sql
from psycopg2.extras import execute_values

from . import thc_client
from .thc_client import FUNCTIONS, call_function
from .thc_db import apply_schema, connect


_IDENTIFIER_RE = re.compile(r"[^a-z0-9_]+")
SYNC_LEADERBOARD_RECORD_LIMIT = 10
SYNC_LANEBANDIT_RECORD_LIMIT = 10
SYNC_COMPETITION_LIST_LIMIT = 100
SYNC_SKIP_FUNCTIONS = {
    "competitions_upcoming": "used only as source ids for query_competitions",
    "competitions_previous": "replaced by query_competitions",
    "leaderboards_hunterscore": "disabled by sync configuration",
}
ROOT_TABLE_OVERRIDES = {
    "competition_detail": "query_competitions",
    "competition_states": "query_player_competition_state",
}


def _identifier(value: str, prefix: str = "") -> str:
    name = _IDENTIFIER_RE.sub("_", value.lower()).strip("_")
    return f"{prefix}{name}"[:63]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _is_collection_dict(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    return all(str(key).isdigit() for key in value)


def _child_table(parent_table: str, path: str) -> str:
    return _identifier(f"{parent_table}_{path}")


def _expand_record(
    value: Any,
    table: str,
    record_id: int,
    tables: dict[str, list[dict[str, Any]]],
    parents: dict[str, str],
) -> dict[str, Any]:
    row: dict[str, Any] = {}
    if not isinstance(value, dict):
        row["scalar_value"] = _text(value)
        return row
    for key, item in value.items():
        if isinstance(item, list) or _is_collection_dict(item):
            _expand_collection(item, table, record_id, str(key), tables, parents)
        elif isinstance(item, dict):
            nested = _expand_record(item, table, record_id, tables, parents)
            for nested_key, nested_value in nested.items():
                row[_identifier(f"{key}_{nested_key}", "field_")] = nested_value
        else:
            row[_identifier(str(key), "field_")] = _text(item)
    return row


def _expand_collection(
    value: Any,
    parent_table: str,
    parent_record_id: int,
    path: str,
    tables: dict[str, list[dict[str, Any]]],
    parents: dict[str, str],
) -> None:
    table = _child_table(parent_table, path)
    parents[table] = parent_table
    items = list(value.items()) if isinstance(value, dict) else list(enumerate(value))
    for index, (item_key, item) in enumerate(items):
        record_id = len(tables[table]) + 1
        row = {
            "record_id": record_id,
            "parent_record_id": parent_record_id,
            "item_index": index,
            "item_key": _text(item_key) if isinstance(value, dict) else None,
        }
        row.update(_expand_record(item, table, record_id, tables, parents))
        tables[table].append(row)


def _tables(value: Any, root_table: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    tables: dict[str, list[dict[str, Any]]] = defaultdict(list)
    parents: dict[str, str] = {}
    if isinstance(value, list) or _is_collection_dict(value):
        source = list(value.items()) if isinstance(value, dict) else list(enumerate(value))
    else:
        source = [(None, value)]
    for record_no, (item_key, item) in enumerate(source):
        record_id = len(tables[root_table]) + 1
        row = {
            "record_id": record_id,
            "root_record_no": record_no,
            "item_key": _text(item_key) if isinstance(value, dict) else None,
        }
        row.update(_expand_record(item, root_table, record_id, tables, parents))
        tables[root_table].append(row)
    return dict(tables), parents


def _create_table(
    cursor: Any,
    table: str,
    fixed_columns: list[tuple[str, str]],
    rows: list[dict[str, Any]],
    parent_table: str | None = None,
) -> list[str]:
    fixed_names = [name for name, _ in fixed_columns]
    dynamic_names = sorted({key for row in rows for key in row} - set(fixed_names))
    columns = fixed_columns + [(name, "text") for name in dynamic_names]
    cursor.execute(
        sql.SQL("CREATE TABLE api.{} ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(
                sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(kind))
                for name, kind in columns
            ),
        )
    )
    if parent_table:
        cursor.execute(
            sql.SQL(
                "ALTER TABLE api.{} ADD FOREIGN KEY (parent_record_id) "
                "REFERENCES api.{} (record_id)"
            ).format(sql.Identifier(table), sql.Identifier(parent_table))
        )
    return [name for name, _ in columns]


def _insert_rows(cursor: Any, table: str, columns: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    statement = sql.SQL("INSERT INTO api.{} ({}) VALUES %s").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )
    execute_values(cursor, statement.as_string(cursor), [tuple(row.get(column) for column in columns) for row in rows])


_WEAPON_STATS_SOURCES = {
    "query_user_by_hostname_weapon": ("query_user_by_hostname_weapon_stats", "query_user_by_hostname"),
    "query_statistics_lifetime_weapon": ("query_statistics_lifetime_weapon_stats", "query_statistics_lifetime"),
    "query_statistics_last_hunt_weapon": ("query_statistics_last_hunt_weapon_stats", "query_statistics_last_hunt"),
}
_WEAPON_STAT_METRICS = ("distance", "ethical_kills", "hits", "kills", "misses")
_WEAPON_FIELD_RE = re.compile(r"^field_([0-9]+)_field_(distance|ethical_kills|hits|kills|misses)$")


def _number_text(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _int_text(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(int(float(str(value))))


def _weapon_stats_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weapon_ids = sorted({
        int(match.group(1))
        for row in rows
        for key in row
        if (match := _WEAPON_FIELD_RE.match(key))
    })
    stats_rows: list[dict[str, Any]] = []
    for row in rows:
        for weapon_id in weapon_ids:
            values = {
                "distance": _number_text(row.get(f"field_{weapon_id}_field_distance")),
                "ethical_kills": _int_text(row.get(f"field_{weapon_id}_field_ethical_kills")),
                "hits": _int_text(row.get(f"field_{weapon_id}_field_hits")),
                "kills": _int_text(row.get(f"field_{weapon_id}_field_kills")),
                "misses": _int_text(row.get(f"field_{weapon_id}_field_misses")),
            }
            if not any(value is not None for value in values.values()):
                continue
            stats_rows.append({
                "source_record_id": row["record_id"],
                "parent_record_id": row["parent_record_id"],
                "item_index": row.get("item_index"),
                "item_key": row.get("item_key"),
                "weapon_id": weapon_id,
                **values,
            })
    return stats_rows


def _create_weapon_stats_table(cursor: Any, table: str, source_table: str, root_table: str) -> list[str]:
    columns = [
        ("source_record_id", "bigint NOT NULL"),
        ("parent_record_id", "bigint NOT NULL"),
        ("item_index", "integer"),
        ("item_key", "text"),
        ("weapon_id", "integer NOT NULL"),
        ("distance", "numeric"),
        ("ethical_kills", "integer"),
        ("hits", "integer"),
        ("kills", "integer"),
        ("misses", "integer"),
        ("PRIMARY KEY", "(source_record_id, weapon_id)"),
    ]
    cursor.execute(
        sql.SQL("CREATE TABLE api.{} ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(
                sql.SQL("PRIMARY KEY (source_record_id, weapon_id)")
                if name == "PRIMARY KEY"
                else sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(kind))
                for name, kind in columns
            ),
        )
    )
    cursor.execute(
        sql.SQL("ALTER TABLE api.{} ADD CONSTRAINT {} FOREIGN KEY (source_record_id) REFERENCES api.{} (record_id)").format(
            sql.Identifier(table),
            sql.Identifier(f"{table}_source_fk"),
            sql.Identifier(source_table),
        )
    )
    cursor.execute(
        sql.SQL("ALTER TABLE api.{} ADD CONSTRAINT {} FOREIGN KEY (parent_record_id) REFERENCES api.{} (record_id)").format(
            sql.Identifier(table),
            sql.Identifier(f"{table}_parent_fk"),
            sql.Identifier(root_table),
        )
    )
    cursor.execute(sql.SQL("CREATE INDEX {} ON api.{} (parent_record_id)").format(sql.Identifier(f"idx_{table}_parent"[:63]), sql.Identifier(table)))
    cursor.execute(sql.SQL("CREATE INDEX {} ON api.{} (weapon_id)").format(sql.Identifier(f"idx_{table}_weapon"[:63]), sql.Identifier(table)))
    return [name for name, _ in columns if name != "PRIMARY KEY"]


def _create_and_fill_weapon_stats(cursor: Any, tables: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for source_table, (stats_table, root_table) in _WEAPON_STATS_SOURCES.items():
        source_rows = tables.get(source_table)
        if not source_rows:
            continue
        stats_rows = _weapon_stats_rows(source_rows)
        columns = _create_weapon_stats_table(cursor, stats_table, source_table, root_table)
        _insert_rows(cursor, stats_table, columns, stats_rows)
        counts[stats_table] = len(stats_rows)
    return counts


def _drop_query_tables(cursor: Any, root_table: str) -> None:
    cursor.execute(
        """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'api' AND tablename LIKE %s
        ORDER BY length(tablename) DESC
        """,
        (f"{root_table}%",),
    )
    for (table,) in cursor.fetchall():
        cursor.execute(
            sql.SQL("DROP TABLE api.{} CASCADE").format(sql.Identifier(table))
        )


def _drop_legacy_competition_tables(cursor: Any) -> None:
    cursor.execute(
        """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'api'
          AND (
            tablename LIKE 'query_competition_%'
            OR tablename LIKE 'query_competitions_previous%'
            OR tablename LIKE 'query_competitions_upcoming%'
          )
        ORDER BY length(tablename) DESC
        """
    )
    for (table,) in cursor.fetchall():
        cursor.execute(
            sql.SQL("DROP TABLE api.{} CASCADE").format(sql.Identifier(table))
        )


def _root_table(function_name: str) -> str:
    return ROOT_TABLE_OVERRIDES.get(function_name, _identifier(function_name, "query_"))


def _default_params(
    function_name: str,
    user_id: int,
    lang: str,
    oauth_access_token: str | None,
) -> dict[str, Any] | None:
    params: dict[str, Any] = {}
    for item in FUNCTIONS[function_name]["params"]:
        name = item["name"]
        if name == "oauth_access_token":
            if not oauth_access_token:
                return None
            params[name] = oauth_access_token
        elif name == "user_id":
            params[name] = user_id
        elif name == "lang":
            params[name] = lang
        else:
            params[name] = item["default"]
    return params


def _competition_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict) and isinstance(value.get("competitions"), list):
        return [item for item in value["competitions"] if isinstance(item, dict)]
    return []


def _competition_id(value: dict[str, Any]) -> Any:
    return value.get("id") or value.get("competition_id")


def _limit_records(value: Any, limit: int) -> Any:
    if isinstance(value, list):
        return [_limit_records(item, limit) for item in value]
    if not isinstance(value, dict):
        return value
    limited = dict(value)
    records = limited.get("records")
    if isinstance(records, list):
        limited["records"] = records[:limit]
    return limited


def _limit_list_key(value: Any, key: str, limit: int) -> Any:
    if isinstance(value, list):
        return value[:limit]
    if not isinstance(value, dict):
        return value
    limited = dict(value)
    rows = limited.get(key)
    if isinstance(rows, list):
        limited[key] = rows[:limit]
        limited[f"{key}_count"] = len(limited[key])
    return limited


def _unfinished_competitions(value: Any, limit: int) -> list[dict[str, Any]]:
    rows = _competition_rows(value)
    unfinished = [
        row
        for row in rows
        if str(row.get("finished", "0")).lower() in {"0", "false", ""}
    ]
    return unfinished[:limit]


def _without_competition_history(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    cleaned = dict(value)
    cleaned.pop("competitions", None)
    return cleaned


def _sync_all_competition_details(lang: str) -> list[dict[str, Any]]:
    seen: set[int] = set()
    details: list[dict[str, Any]] = []
    source = _unfinished_competitions(
        thc_client.get_competitions_upcoming(lang),
        SYNC_COMPETITION_LIST_LIMIT,
    )
    for competition in source:
        competition_id = _competition_id(competition)
        if competition_id in (None, ""):
            continue
        competition_id = int(competition_id)
        if competition_id in seen:
            continue
        seen.add(competition_id)
        detail = thc_client.get_competition_detail(competition_id, lang)
        if isinstance(detail, dict):
            detail = {"competition_id": competition_id, **detail}
        details.append(_without_competition_history(detail))
    return details


def _sync_all_antler_details() -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for antler_type, summaries in (
        ("single", thc_client.get_leaderboards_antlers_single()),
        ("double", thc_client.get_leaderboards_antlers_double()),
    ):
        if not isinstance(summaries, list):
            continue
        for summary in summaries:
            if not isinstance(summary, dict) or summary.get("id") in (None, ""):
                continue
            antler_id = int(summary["id"])
            try:
                detail = thc_client.get_leaderboards_antler_detail(
                    antler_type, antler_id
                )
            except Exception:
                continue
            if isinstance(detail, dict):
                detail = {
                    "antler_type": antler_type,
                    "antler_id": antler_id,
                    **detail,
                }
            details.append(_limit_records(detail, SYNC_LEADERBOARD_RECORD_LIMIT))
    return details


def _sync_query_value(function_name: str, params: dict[str, Any], lang: str) -> Any:
    if function_name in {"leaderboards_score", "leaderboard_details_score"}:
        return _limit_records(
            thc_client.get_leaderboards_score(), SYNC_LEADERBOARD_RECORD_LIMIT
        )
    if function_name in {"leaderboards_range", "leaderboard_details_range"}:
        return _limit_records(
            thc_client.get_leaderboards_range(), SYNC_LEADERBOARD_RECORD_LIMIT
        )
    if function_name == "competitions_upcoming":
        return _unfinished_competitions(
            thc_client.get_competitions_upcoming(lang),
            SYNC_COMPETITION_LIST_LIMIT,
        )
    if function_name == "leaderboards_hall_of_fame":
        return _limit_records(
            call_function(function_name, params), SYNC_LEADERBOARD_RECORD_LIMIT
        )
    if function_name == "leaderboards_lanebandit":
        return thc_client.get_leaderboards_lanebandit(
            params["user_id"], max_records=SYNC_LANEBANDIT_RECORD_LIMIT
        )
    if function_name == "leaderboards_bustthrough":
        return thc_client.get_leaderboards_bustthrough(
            params["user_id"], max_records=SYNC_LEADERBOARD_RECORD_LIMIT
        )
    if function_name == "competition_detail":
        return _sync_all_competition_details(lang)
    if function_name == "leaderboards_antler_detail":
        return _sync_all_antler_details()
    return call_function(function_name, params)


def sync_queries(
    *,
    user_id: int = 29509787,
    lang: str = "es_ES",
    oauth_access_token: str | None = None,
    function_names: list[str] | None = None,
) -> dict[str, Any]:
    """Refresh physical SQL tables for reusable queries without storing JSON."""
    selected = function_names or list(FUNCTIONS)
    connection = connect()
    try:
        with connection:
            apply_schema(connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO api.query_sync_runs (status)
                    VALUES ('running')
                    RETURNING query_sync_run_id
                    """
                )
                sync_run_id = cursor.fetchone()[0]
                stats: dict[str, dict[str, Any]] = {}
                for function_name in selected:
                    if function_name in SYNC_SKIP_FUNCTIONS:
                        stats[function_name] = {
                            "skipped": SYNC_SKIP_FUNCTIONS[function_name]
                        }
                        continue
                    params = _default_params(
                        function_name, user_id, lang, oauth_access_token
                    )
                    if params is None:
                        stats[function_name] = {"skipped": "oauth_access_token required"}
                        continue
                    try:
                        value = _sync_query_value(function_name, params, lang)
                    except Exception as exc:
                        stats[function_name] = {
                            "skipped": f"{type(exc).__name__}: {exc}"
                        }
                        continue
                    root_table = _root_table(function_name)
                    if root_table == "query_competitions":
                        _drop_legacy_competition_tables(cursor)
                    tables, parents = _tables(value, root_table)
                    _drop_query_tables(cursor, root_table)
                    for table, rows in tables.items():
                        if table == root_table:
                            fixed_columns = [
                                ("record_id", "bigint PRIMARY KEY"),
                                ("root_record_no", "bigint"),
                                ("item_key", "text"),
                            ]
                        else:
                            fixed_columns = [
                                ("record_id", "bigint PRIMARY KEY"),
                                ("parent_record_id", "bigint"),
                                ("item_index", "integer"),
                                ("item_key", "text"),
                                ("scalar_value", "text"),
                            ]
                        columns = _create_table(
                            cursor,
                            table,
                            fixed_columns,
                            rows,
                            parents.get(table),
                        )
                        _insert_rows(cursor, table, columns, rows)
                    weapon_stats_counts = _create_and_fill_weapon_stats(cursor, tables)
                    child_tables = [table for table in tables if table != root_table]
                    child_tables.extend(weapon_stats_counts)
                    derived_table = ", ".join(child_tables)
                    root_records = len(tables[root_table])
                    derived_records = sum(len(tables[table]) for table in tables if table != root_table) + sum(weapon_stats_counts.values())
                    cursor.execute(
                        """
                        INSERT INTO api.query_table_stats (
                            query_sync_run_id, function_name, root_table,
                            derived_table, root_records, derived_records
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            sync_run_id,
                            function_name,
                            root_table,
                            derived_table,
                            root_records,
                            derived_records,
                        ),
                    )
                    stats[function_name] = {
                        "root_table": root_table,
                        "derived_tables": child_tables,
                        "root_records": root_records,
                        "derived_records": derived_records,
                        "weapon_stats_tables": weapon_stats_counts,
                    }
                cursor.execute(
                    """
                    UPDATE api.query_sync_runs
                    SET completed_at = now(), status = 'completed', functions_count = %s
                    WHERE query_sync_run_id = %s
                    """,
                    (len(stats), sync_run_id),
                )
        return {"query_sync_run_id": sync_run_id, "functions": stats}
    finally:
        connection.close()
