import os
import sys
from pathlib import Path

import psycopg2

def read_sql(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_sql.py path/to/file.sql [path2.sql ...]")
        sys.exit(2)

    pg_url = os.getenv("PG_URL")
    if not pg_url:
        raise SystemExit("Missing PG_URL. Example: export PG_URL='postgresql://user:pwd@localhost:5432/loan_demo'")

    sql_files = [Path(a) for a in sys.argv[1:]]
    for f in sql_files:
        if not f.exists():
            raise SystemExit(f"SQL file not found: {f}")

    conn = psycopg2.connect(pg_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for f in sql_files:
                print(f"▶ Running: {f}")
                cur.execute(read_sql(f))
                print("  ✅ OK")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
