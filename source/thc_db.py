"""PostgreSQL persistence for the official theHunter Classic catalogs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

import psycopg2
from psycopg2.extras import Json, execute_values

from .thc_catalog_loader import load_normalized

from .thc_client import get_application_data


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
LANG_TABLES = (
    "bundle_items",
    "mission_group_reserves",
    "mission_group_weapons",
    "mission_group_species",
    "mission_group_missions",
    "mission_dependencies",
    "mission_reserves",
    "mission_weapons",
    "mission_species",
    "reserve_species",
    "tutorials",
    "bundles",
    "dog_skills",
    "rank_categories",
    "achievement_categories",
    "achievements",
    "collectables",
    "mission_groups",
    "missions",
    "locations",
    "reserves",
    "species",
    "items",
    "item_subcategories",
    "item_categories",
    "catalog_entries",
)


class ThcDatabaseError(RuntimeError):
    """Raised when catalog persistence cannot be completed."""


def connect() -> Any:
    """Connect using environment variables without persisting credentials."""
    password = os.environ.get("THC_DB_PASSWORD")
    if not password:
        raise ThcDatabaseError("THC_DB_PASSWORD environment variable is required")
    return psycopg2.connect(
        host=os.environ.get("THC_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("THC_DB_PORT", "5432")),
        dbname=os.environ.get("THC_DB_NAME", "thc_api"),
        user=os.environ.get("THC_DB_USER", "postgres"),
        password=password,
    )


def apply_schema(connection: Any) -> None:
    """Create the catalog schema, tables and views when needed."""
    connection.cursor().execute(SCHEMA_PATH.read_text(encoding="utf-8"))


def _insert_values(
    cursor: Any,
    table: str,
    columns: tuple[str, ...],
    rows: Iterable[tuple[Any, ...]],
) -> int:
    values = list(rows)
    if not values:
        return 0
    execute_values(
        cursor,
        f"INSERT INTO api.{table} ({', '.join(columns)}) VALUES %s",
        values,
    )
    return len(values)


def _records(value: Any) -> list[tuple[str, Any]]:
    if isinstance(value, list):
        return [
            (str(item.get("id", index)) if isinstance(item, dict) else str(index), item)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        return [
            (
                str(item.get("id", key)) if isinstance(item, dict) else str(key),
                item,
            )
            for key, item in value.items()
        ]
    return [("value", value)]


def _relation_rows(
    records: Iterable[dict[str, Any]],
    owner_key: str,
    relation_key: str,
    lang: str,
    sync_run_id: int,
) -> Iterable[tuple[Any, Any, str, int]]:
    for record in records:
        for relation_id in record.get(relation_key, []) or []:
            yield record[owner_key], relation_id, lang, sync_run_id


def _clear_language(cursor: Any, lang: str) -> None:
    for table in LANG_TABLES:
        cursor.execute(f"DELETE FROM api.{table} WHERE lang = %s", (lang,))


def _load_generic_entries(
    cursor: Any, catalogs: dict[str, Any], lang: str, sync_run_id: int
) -> int:
    return _insert_values(
        cursor,
        "catalog_entries",
        ("catalog_name", "external_id", "lang", "payload", "sync_run_id"),
        (
            (catalog_name, external_id, lang, Json(payload), sync_run_id)
            for catalog_name, value in catalogs.items()
            for external_id, payload in _records(value)
        ),
    )


def _load_normalized(
    cursor: Any, catalogs: dict[str, Any], lang: str, sync_run_id: int
) -> dict[str, int]:
    return load_normalized(
        cursor,
        catalogs,
        lang,
        sync_run_id,
        _insert_values,
        _records,
        _relation_rows,
    )


def sync_catalogs(lang: str = "es_ES") -> dict[str, Any]:
    """Fetch and atomically replace one locale's official static catalogs."""
    catalogs = get_application_data(lang)
    connection = connect()
    try:
        with connection:
            apply_schema(connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO api.catalog_sync_runs (lang, status)
                    VALUES (%s, 'running')
                    RETURNING sync_run_id
                    """,
                    (lang,),
                )
                sync_run_id = cursor.fetchone()[0]
                _clear_language(cursor, lang)
                generic_entries = _load_generic_entries(
                    cursor, catalogs, lang, sync_run_id
                )
                table_counts = _load_normalized(cursor, catalogs, lang, sync_run_id)
                cursor.execute(
                    """
                    UPDATE api.catalog_sync_runs
                    SET completed_at = now(),
                        status = 'completed',
                        catalogs_count = %s,
                        entries_count = %s
                    WHERE sync_run_id = %s
                    """,
                    (len(catalogs), generic_entries, sync_run_id),
                )
        return {
            "sync_run_id": sync_run_id,
            "lang": lang,
            "catalogs": len(catalogs),
            "catalog_entries": generic_entries,
            "tables": table_counts,
        }
    except Exception as exc:
        raise ThcDatabaseError(f"Catalog synchronization failed: {exc}") from exc
    finally:
        connection.close()
