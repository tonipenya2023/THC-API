"""Synchronize reusable theHunter API queries into PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from source.thc_query_db import sync_queries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=29509787)
    parser.add_argument("--lang", default="es_ES")
    parser.add_argument("--oauth-access-token")
    parser.add_argument("--function", action="append", dest="functions")
    args = parser.parse_args()
    print(
        json.dumps(
            sync_queries(
                user_id=args.user_id,
                lang=args.lang,
                oauth_access_token=args.oauth_access_token,
                function_names=args.functions,
            ),
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
