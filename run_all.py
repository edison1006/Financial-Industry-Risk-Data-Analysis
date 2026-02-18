import subprocess
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent

def run(cmd):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))

def main():
    if not os.getenv("PG_URL"):
        raise SystemExit("Missing PG_URL. Example: export PG_URL='postgresql://user:pwd@localhost:5432/loan_demo'")

    run(["python", "run_core.py"])
    run(["python", "run_risk.py"])
    run(["python", "run_commercial.py"])

    print("\n🎉 All done. Import these views into Power BI:")
    print("- loan_analytics.mart_portfolio_snapshot_v2")
    print("- loan_analytics.mart_dpd_migration")
    print("- loan_analytics.risk_watchlist")
    print("- loan_analytics.comm_rar_monthly")

if __name__ == "__main__":
    main()
