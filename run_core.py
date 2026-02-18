import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(cmd, cwd=None):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)

def main():
    # Require PG_URL
    if not os.getenv("PG_URL"):
        raise SystemExit("Missing PG_URL. Example: export PG_URL='postgresql://user:pwd@localhost:5432/loan_demo'")

    core_py = ROOT / "core" / "python"
    core_sql = ROOT / "core" / "sql"

    # 1) Install deps
    run(["python", "-m", "pip", "install", "-r", str(core_py / "requirements.txt")], cwd=str(core_py))

    # 2) Create tables
    run(["python", str(core_py / "run_sql.py"), str(core_sql / "01_schema_postgres.sql")], cwd=str(core_py))

    # 3) Generate + load data
    run(["python", str(core_py / "run_pipeline.py")], cwd=str(core_py))

    # 4) Create marts
    run(["python", str(core_py / "run_sql.py"),
         str(core_sql / "03_mart_views.sql"),
         str(core_sql / "03_mart_views_plus_balance.sql")], cwd=str(core_py))

    print("\n✅ Core pipeline complete.")
    print("Try: SELECT COUNT(*) FROM loan_analytics.fct_loans;")

if __name__ == "__main__":
    main()
