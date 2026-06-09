"""Generic PostgreSQL persistence for reusable theHunter API queries."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from psycopg2 import sql
from psycopg2.extras import execute_values

from source.thc_client import FUNCTIONS, call_function
from source.thc_db import apply_schema, connect


_IDENTIFIER_RE = re.compile(r"[^a-z0-9_]+")


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
        elif function_name == "statistics_history" and name == "limit":
            params[name] = 1000
        else:
            params[name] = item["default"]
    return params


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
                    params = _default_params(
                        function_name, user_id, lang, oauth_access_token
                    )
                    if params is None:
                        stats[function_name] = {"skipped": "oauth_access_token required"}
                        continue
                    try:
                        value = call_function(function_name, params)
                    except Exception as exc:
                        stats[function_name] = {
                            "skipped": f"{type(exc).__name__}: {exc}"
                        }
                        continue
                    root_table = _identifier(function_name, "query_")
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
                    child_tables = [table for table in tables if table != root_table]
                    derived_table = ", ".join(child_tables)
                    root_records = len(tables[root_table])
                    derived_records = sum(len(tables[table]) for table in child_tables)
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
