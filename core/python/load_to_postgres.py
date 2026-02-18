import os
import pandas as pd
from sqlalchemy import create_engine, text

RAW_DIR = "../data/raw"
SCHEMA = "loan_analytics"

def load_csv(engine, table_name: str, csv_path: str):
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, schema=SCHEMA, if_exists="append", index=False, method="multi", chunksize=2000)
    print(f"Loaded {table_name}: {len(df):,}")

def main():
    pg_url = os.getenv("PG_URL")
    if not pg_url:
        raise ValueError("Set env var PG_URL, e.g. export PG_URL='postgresql://user:pwd@localhost:5432/db'")

    engine = create_engine(pg_url)

    with engine.begin() as conn:
        conn.execute(text(f"SET search_path TO {SCHEMA};"))
        conn.execute(text("TRUNCATE TABLE fct_collections RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE fct_payments RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE fct_schedule RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE fct_loans RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE dim_customers RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE dim_products RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE dim_channels RESTART IDENTITY CASCADE;"))

    load_csv(engine, "dim_customers", os.path.join(RAW_DIR, "dim_customers.csv"))
    load_csv(engine, "dim_products", os.path.join(RAW_DIR, "dim_products.csv"))
    load_csv(engine, "dim_channels", os.path.join(RAW_DIR, "dim_channels.csv"))
    load_csv(engine, "fct_loans", os.path.join(RAW_DIR, "fct_loans.csv"))
    load_csv(engine, "fct_schedule", os.path.join(RAW_DIR, "fct_schedule.csv"))
    load_csv(engine, "fct_payments", os.path.join(RAW_DIR, "fct_payments.csv"))
    load_csv(engine, "fct_collections", os.path.join(RAW_DIR, "fct_collections.csv"))

    print("✅ Done.")

if __name__ == "__main__":
    main()
