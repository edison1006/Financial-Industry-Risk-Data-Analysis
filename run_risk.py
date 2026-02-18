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
    risk_sql = ROOT / "package_risk" / "sql"
    risk_py = ROOT / "package_risk" / "python"

    # ensure deps installed (includes scikit-learn)
    run(["python", "-m", "pip", "install", "-r", str(core_py / "requirements.txt")], cwd=str(core_py))

    # 1) Create features + labels
    run(["python", str(core_py / "run_sql.py"), str(risk_sql / "10_risk_features.sql")], cwd=str(core_py))

    # 2) Train model -> writes loan_analytics.risk_scores
    run(["python", str(risk_py / "train_risk_model.py")], cwd=str(ROOT))

    # 3) Create watchlist view
    run(["python", str(core_py / "run_sql.py"), str(risk_sql / "11_risk_score_view.sql")], cwd=str(core_py))

    print("\n✅ Risk package complete.")
    print("Try: SELECT * FROM loan_analytics.risk_watchlist LIMIT 10;")

if __name__ == "__main__":
    main()
