"""External throttled dashboard refresh worker."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from source.thc_db import apply_schema, connect
from source.thc_query_db import sync_queries


SQL_DIR = PROJECT_ROOT / "sql"
VIEW_SQL_PATHS = [
    SQL_DIR / "dashboard_views.sql",
    SQL_DIR / "vistas_rangos.sql",
    SQL_DIR / "grafana_domain_views.sql",
]
DEFAULT_REFRESH_KEY = "grafana_competitions"
DEFAULT_FUNCTIONS = ["competition_detail"]


def _claim_refresh(refresh_key: str | None) -> dict[str, Any] | None:
    connection = connect()
    try:
        with connection:
            apply_schema(connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT refresh_key, functions
                    FROM api.dashboard_refresh_control
                    WHERE status = 'queued'
                      AND (%s IS NULL OR refresh_key = %s)
                    ORDER BY requested_at NULLS FIRST, updated_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """,
                    (refresh_key, refresh_key),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                claimed_key, functions = row
                cursor.execute(
                    """
                    UPDATE api.dashboard_refresh_control
                    SET status = 'running',
                        started_at = now(),
                        last_attempted_at = now(),
                        error_message = NULL,
                        updated_at = now()
                    WHERE refresh_key = %s
                    """,
                    (claimed_key,),
                )
        return {"refresh_key": claimed_key, "functions": list(functions or DEFAULT_FUNCTIONS)}
    finally:
        connection.close()


def _mark_refresh_ok(refresh_key: str, query_sync_run_id: int) -> None:
    connection = connect()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE api.dashboard_refresh_control
                    SET status = 'ok',
                        last_completed_at = now(),
                        last_query_sync_run_id = %s,
                        error_message = NULL,
                        updated_at = now()
                    WHERE refresh_key = %s
                    """,
                    (query_sync_run_id, refresh_key),
                )
    finally:
        connection.close()


def _mark_refresh_failed(refresh_key: str, exc: BaseException) -> None:
    connection = connect()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE api.dashboard_refresh_control
                    SET status = 'failed',
                        error_message = %s,
                        updated_at = now()
                    WHERE refresh_key = %s
                    """,
                    (f"{type(exc).__name__}: {exc}"[:1000], refresh_key),
                )
    finally:
        connection.close()


def run_once(args: argparse.Namespace) -> bool:
    job = _claim_refresh(args.refresh_key)
    if job is None:
        return False

    refresh_key = job["refresh_key"]
    functions = job["functions"]
    print(f"Running refresh {refresh_key}: {', '.join(functions)}", flush=True)
    try:
        result = sync_queries(
            user_id=args.user_id,
            lang=args.lang,
            oauth_access_token=args.oauth_access_token,
            function_names=functions,
            apply_view_sql_paths=VIEW_SQL_PATHS,
        )
        skipped = {
            name: stats["skipped"]
            for name, stats in result.get("functions", {}).items()
            if isinstance(stats, dict) and "skipped" in stats
        }
        if skipped:
            raise RuntimeError(f"Refresh skipped functions: {skipped}")
        query_sync_run_id = int(result["query_sync_run_id"])
        _mark_refresh_ok(refresh_key, query_sync_run_id)
        print(f"Refresh {refresh_key} completed with query_sync_run_id={query_sync_run_id}", flush=True)
        return True
    except BaseException as exc:
        _mark_refresh_failed(refresh_key, exc)
        print(f"Refresh {refresh_key} failed: {type(exc).__name__}: {exc}", flush=True)
        if args.once:
            raise
        return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-key", default=DEFAULT_REFRESH_KEY)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--user-id", type=int, default=29509787)
    parser.add_argument("--lang", default="es_ES")
    parser.add_argument("--oauth-access-token", default=os.environ.get("THC_OAUTH_ACCESS_TOKEN"))
    args = parser.parse_args()

    while True:
        processed = run_once(args)
        if args.once:
            return
        if not processed:
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
