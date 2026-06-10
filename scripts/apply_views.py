"""Apply analytical views to PostgreSQL for the THC Dashboard."""

import os
from pathlib import Path

import psycopg2


SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
SCHEMA_PATH = SQL_DIR / "schema.sql"
SQL_PATHS = [
    SQL_DIR / "dashboard_views.sql",
    SQL_DIR / "vistas_rangos.sql",
    SQL_DIR / "grafana_domain_views.sql",
]


def main() -> None:
    password = os.environ.get("THC_DB_PASSWORD", "system")
    try:
        conn = psycopg2.connect(
            host=os.environ.get("THC_DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("THC_DB_PORT", "5432")),
            dbname=os.environ.get("THC_DB_NAME", "thc_api"),
            user=os.environ.get("THC_DB_USER", "postgres"),
            password=password
        )
        cursor = conn.cursor()

        print(f"Applying {SCHEMA_PATH}...")
        cursor.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        
        for sql_path in SQL_PATHS:
            print(f"Applying {sql_path}...")
            cursor.execute(sql_path.read_text(encoding="utf-8"))
        conn.commit()
        print("Views successfully applied!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error applying dashboard views:", e)

if __name__ == "__main__":
    main()
