"""Synchronize official theHunter Classic catalogs into PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from source.thc_db import sync_catalogs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="es_ES")
    args = parser.parse_args()
    print(json.dumps(sync_catalogs(args.lang), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
