"""
Execute SQL files using SQLAlchemy (supports multiple database engines).
"""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

def read_sql(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _strip_sql_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_sql.py path/to/file.sql [path2.sql ...]")
        sys.exit(2)

    # Support multiple connection string formats
    db_url = os.getenv("DB_URL") or os.getenv("PG_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit(
            "Missing database connection. Set DB_URL environment variable.\n"
            "Examples:\n"
            "  DB_URL='sqlite:///loan_demo.db'\n"
            "  DB_URL='mysql+pymysql://user:password@localhost:3306/loan_demo'\n"
            "  DB_URL='mssql+pyodbc://user:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server'\n"
            "  DB_URL='postgresql://user:password@localhost:5432/loan_demo'"
        )

    sql_files = [Path(a) for a in sys.argv[1:]]
    for f in sql_files:
        if not f.exists():
            raise SystemExit(f"SQL file not found: {f}")

    engine = create_engine(db_url)
    try:
        # SQLite: use a raw DB-API connection for executescript
        if engine.dialect.name == "sqlite":
            raw = engine.raw_connection()
            try:
                for f in sql_files:
                    print(f"> Running: {f}")
                    sql_content = _strip_sql_comments(read_sql(f))
                    raw.executescript(sql_content)
                    raw.commit()
                    print("  OK")
            finally:
                raw.close()
        else:
            with engine.begin() as conn:
                for f in sql_files:
                    print(f"> Running: {f}")
                    sql_content = _strip_sql_comments(read_sql(f))
                    statements = [s.strip() for s in sql_content.split(";") if s.strip()]
                    for stmt in statements:
                        conn.execute(text(stmt))
                    print("  OK")
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
