"""
Load CSV data to database using SQLAlchemy (supports multiple database engines).
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

RAW_DIR = "../data/raw"


def _table(name: str) -> str:
    # SQLite-friendly: tables are created without schema prefix
    return name

def load_csv(engine, table_name: str, csv_path: str):
    df = pd.read_csv(csv_path)
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=2000
    )
    print(f"Loaded {table_name}: {len(df):,}")

def main():
    # Support multiple connection string formats
    db_url = os.getenv("DB_URL") or os.getenv("PG_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "Set DB_URL environment variable.\n"
            "Examples:\n"
            "  DB_URL='sqlite:///loan_demo.db'\n"
            "  DB_URL='mysql+pymysql://user:password@localhost:3306/loan_demo'\n"
            "  DB_URL='mssql+pyodbc://user:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server'\n"
            "  DB_URL='postgresql://user:password@localhost:5432/loan_demo'"
        )

    engine = create_engine(db_url)

    with engine.begin() as conn:
        # Clear existing data (SQLite-friendly)
        conn.execute(text(f"DELETE FROM {_table('fct_collections')}"))
        conn.execute(text(f"DELETE FROM {_table('fct_payments')}"))
        conn.execute(text(f"DELETE FROM {_table('fct_schedule')}"))
        conn.execute(text(f"DELETE FROM {_table('fct_loans')}"))
        conn.execute(text(f"DELETE FROM {_table('dim_customers')}"))
        conn.execute(text(f"DELETE FROM {_table('dim_products')}"))
        conn.execute(text(f"DELETE FROM {_table('dim_channels')}"))

    load_csv(engine, _table("dim_customers"), os.path.join(RAW_DIR, "dim_customers.csv"))
    load_csv(engine, _table("dim_products"), os.path.join(RAW_DIR, "dim_products.csv"))
    load_csv(engine, _table("dim_channels"), os.path.join(RAW_DIR, "dim_channels.csv"))
    load_csv(engine, _table("fct_loans"), os.path.join(RAW_DIR, "fct_loans.csv"))
    load_csv(engine, _table("fct_schedule"), os.path.join(RAW_DIR, "fct_schedule.csv"))
    load_csv(engine, _table("fct_payments"), os.path.join(RAW_DIR, "fct_payments.csv"))
    load_csv(engine, _table("fct_collections"), os.path.join(RAW_DIR, "fct_collections.csv"))

    print("Done.")

if __name__ == "__main__":
    main()
