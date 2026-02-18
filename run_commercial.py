import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(cmd, cwd=None):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)

def main():
    if not os.getenv("PG_URL"):
        raise SystemExit("Missing PG_URL. Example: export PG_URL='postgresql://user:pwd@localhost:5432/loan_demo'")

    core_py = ROOT / "core" / "python"
    comm_sql = ROOT / "package_commercial" / "sql"

    run(["python", "-m", "pip", "install", "-r", str(core_py / "requirements.txt")], cwd=str(core_py))
    run(["python", str(core_py / "run_sql.py"), str(comm_sql / "20_commercial_marts.sql")], cwd=str(core_py))

    print("\n✅ Commercial package complete.")
    print("Try: SELECT SUM(rar_profit_est) FROM loan_analytics.comm_rar_monthly;")

if __name__ == "__main__":
    main()
