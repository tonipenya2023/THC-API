"""Synchronize THC queries one by one and record elapsed time per function."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from source.thc_client import FUNCTIONS
from source.thc_query_db import sync_queries


def _function_names(selected: list[str] | None) -> list[str]:
    if selected:
        return selected
    return list(FUNCTIONS)


def _status(function_result: dict[str, Any]) -> str:
    if "skipped" in function_result:
        return "SKIPPED"
    return "OK"


def _row_from_result(
    index: int,
    total: int,
    name: str,
    elapsed_seconds: float,
    result: dict[str, Any],
) -> dict[str, Any]:
    functions = result.get("functions", {}) if isinstance(result, dict) else {}
    function_result = functions.get(name, {}) if isinstance(functions, dict) else {}
    return {
        "index": index,
        "total": total,
        "function": name,
        "status": _status(function_result) if isinstance(function_result, dict) else "UNKNOWN",
        "seconds": round(elapsed_seconds, 3),
        "root_table": function_result.get("root_table") if isinstance(function_result, dict) else "",
        "root_records": function_result.get("root_records") if isinstance(function_result, dict) else "",
        "derived_records": function_result.get("derived_records") if isinstance(function_result, dict) else "",
        "skipped": function_result.get("skipped", "") if isinstance(function_result, dict) else "",
    }


def _write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = ["#", "Funcion", "Estado", "Segundos", "Root", "Derivados", "Nota"]
    table_rows = [
        [
            f"{row['index']}/{row['total']}",
            str(row["function"]),
            str(row["status"]),
            str(row["seconds"]),
            str(row["root_records"]),
            str(row["derived_records"]),
            str(row["skipped"]),
        ]
        for row in rows
    ]
    widths = [
        max(len(headers[column]), *(len(row[column]) for row in table_rows))
        if table_rows
        else len(headers[column])
        for column in range(len(headers))
    ]

    def _cell(value: str, column: int, right: bool = False) -> str:
        return value.rjust(widths[column]) if right else value.ljust(widths[column])

    def _line(values: list[str]) -> str:
        return (
            "| "
            + " | ".join(
                _cell(value, index, right=index in {0, 3, 4, 5})
                for index, value in enumerate(values)
            )
            + " |"
        )

    lines = [
        "# Tiempos sync queries",
        "",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        _line(headers),
        "| "
        + " | ".join(
            ("-" * (widths[index] - 1) + ":")
            if index in {0, 3, 4, 5}
            else "-" * widths[index]
            for index in range(len(headers))
        )
        + " |",
    ]
    lines.extend(_line(row) for row in table_rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _start_heartbeat(name: str, start: float, seconds: int) -> tuple[threading.Event, threading.Thread | None]:
    if seconds <= 0:
        return threading.Event(), None

    stop = threading.Event()

    def _run() -> None:
        while not stop.wait(seconds):
            elapsed = round(time.monotonic() - start, 1)
            print(f"[RUNNING] {name} elapsed_seconds={elapsed}", flush=True)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return stop, thread


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=29509787)
    parser.add_argument("--lang", default="es_ES")
    parser.add_argument("--oauth-access-token")
    parser.add_argument("--function", action="append", dest="functions")
    parser.add_argument("--heartbeat-seconds", type=int, default=10)
    args = parser.parse_args()

    names = _function_names(args.functions)
    evidence_dir = PROJECT_ROOT / "evidencias"
    evidence_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = evidence_dir / f"sync_tiempos_{stamp}.csv"
    md_path = evidence_dir / f"sync_tiempos_{stamp}.md"
    rows: list[dict[str, Any]] = []

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "index",
            "total",
            "function",
            "status",
            "seconds",
            "root_table",
            "root_records",
            "derived_records",
            "skipped",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for index, name in enumerate(names, start=1):
            print(f"\n[{index}/{len(names)}] START {name}", flush=True)
            start = time.monotonic()
            heartbeat_stop, heartbeat_thread = _start_heartbeat(
                name, start, args.heartbeat_seconds
            )
            try:
                result = sync_queries(
                    user_id=args.user_id,
                    lang=args.lang,
                    oauth_access_token=args.oauth_access_token,
                    function_names=[name],
                )
                elapsed = time.monotonic() - start
                row = _row_from_result(index, len(names), name, elapsed, result)
            except Exception as exc:
                elapsed = time.monotonic() - start
                row = {
                    "index": index,
                    "total": len(names),
                    "function": name,
                    "status": "ERROR",
                    "seconds": round(elapsed, 3),
                    "root_table": "",
                    "root_records": "",
                    "derived_records": "",
                    "skipped": f"{type(exc).__name__}: {exc}",
                }

            heartbeat_stop.set()
            if heartbeat_thread is not None:
                heartbeat_thread.join(timeout=1)
            rows.append(row)
            writer.writerow(row)
            handle.flush()
            print(json.dumps(row, ensure_ascii=True), flush=True)
            _write_markdown(md_path, rows)

    print(f"\nCSV: {csv_path}")
    print(f"MD:  {md_path}")
    if any(row["status"] == "ERROR" for row in rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
