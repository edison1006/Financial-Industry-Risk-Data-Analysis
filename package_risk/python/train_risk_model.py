import os
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support

def main():
    db_url = os.getenv("DB_URL") or os.getenv("PG_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "Set DB_URL environment variable.\n"
            "Examples: DB_URL='sqlite:///loan_demo.db' or DB_URL='mysql+pymysql://user:password@localhost:3306/loan_demo'"
        )

    engine = create_engine(db_url)

    # Performance note: risk_features_3m can be large. Train on a recent window.
    feat = pd.read_sql(
        """
        WITH mx AS (SELECT MAX(month_end) AS mx FROM risk_features_3m)
        SELECT *
        FROM risk_features_3m
        WHERE month_end >= date((SELECT mx FROM mx), '-24 months')
        """,
        engine,
    )
    lab = pd.read_sql(
        """
        WITH mx AS (SELECT MAX(month_end) AS mx FROM risk_labels_60p_3m)
        SELECT *
        FROM risk_labels_60p_3m
        WHERE month_end >= date((SELECT mx FROM mx), '-24 months')
        """,
        engine,
    )
    df = feat.merge(lab, on=["loan_id","month_end"], how="inner")

    # keep rows with enough history
    df = df.dropna(subset=["roll3_paid_full_rate","roll3_avg_arrears"])

    y = df["will_be_60p_in_3m"].astype(int)

    num_cols = ["credit_score","annual_income_nzd","roll3_paid_full_rate","roll3_missed_cnt","roll3_avg_arrears","eop_balance","interest_rate_apr"]
    cat_cols = ["product_type","channel","employment_type","dpd_bucket"]
    X = df[num_cols + cat_cols]

    pre = ColumnTransformer(
        transformers=[
            ("num", "passthrough", num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ]
    )

    model = LogisticRegression(max_iter=300, class_weight="balanced")
    pipe = Pipeline(steps=[("pre", pre), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    y_pred = (proba >= 0.5).astype(int)
    p, r, f, _ = precision_recall_fscore_support(y_test, y_pred, average="binary", zero_division=0)

    print(f"AUC={auc:.3f}  Precision={p:.3f}  Recall={r:.3f}  F1={f:.3f}")

    # score full dataset
    df["risk_score"] = pipe.predict_proba(X)[:, 1]
    out = df[["loan_id","month_end","risk_score","will_be_60p_in_3m"]]
    out.to_sql("risk_scores", engine, if_exists="replace", index=False)
    print("Saved risk_scores")

if __name__ == "__main__":
    main()
