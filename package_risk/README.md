# Package A — Risk / Collections

## What this package delivers
- Monthly delinquency monitoring (30+/60+/90+)
- Roll-rate migration matrix (prev bucket -> current bucket)
- Early-warning model: predict whether a loan will enter **60+** within the next **3 months**
- Watchlist: rank by **risk_score** + **EOP balance** for collections prioritisation

## Setup
1) Run core steps first (schema, data generation, load, baseline marts, plus balance):
- `core/sql/01_schema.sql`
- `core/sql/03_mart_views.sql`
- `core/sql/03_mart_views_plus_balance.sql`

2) Create risk features + labels:
- `package_risk/sql/10_risk_features.sql`

3) Train and write back scores:
```bash
export DB_URL="sqlite:///loan_demo.db"  # Or MySQL, SQL Server, PostgreSQL connection string
python package_risk/python/train_risk_model.py
```

4) Create watchlist view:
- `package_risk/sql/11_risk_score_view.sql`

## Power BI
Import:
- `loan_analytics.mart_portfolio_snapshot_v2`
- `loan_analytics.mart_dpd_migration`
- `loan_analytics.risk_watchlist`

Paste measures from `powerbi/measures_dax.md`.

## Story / Recommendations (what to write in interviews)
- Identify deterioration drivers using migration + segment cuts (product/channel/region).
- Prioritise collections via watchlist: high risk_score + high balance.
- Recommend policy tightening or hardship routing for specific segments.
