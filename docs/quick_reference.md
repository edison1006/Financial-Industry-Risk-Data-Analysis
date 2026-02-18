# Quick Reference Guide

Quick commands and queries for common tasks.

## Setup

### Set Database Connection

**Windows PowerShell:**
```powershell
# SQLite (simplest, no server needed)
$env:DB_URL="sqlite:///loan_demo.db"

# MySQL
$env:DB_URL="mysql+pymysql://username:password@localhost:3306/loan_demo"

# SQL Server
$env:DB_URL="mssql+pyodbc://username:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server"

# PostgreSQL
$env:DB_URL="postgresql://username:password@localhost:5432/loan_demo"
```

**Linux/Mac:**
```bash
# SQLite
export DB_URL="sqlite:///loan_demo.db"

# MySQL
export DB_URL="mysql+pymysql://user:password@localhost:3306/loan_demo"
```

### Manual Steps

```bash
# 1. Install dependencies
cd core/python
pip install -r requirements.txt

# 2. Create schema
python run_sql.py ../sql/01_schema.sql

# 3. Generate and load data
python run_pipeline.py

# 4. Build baseline marts
python run_sql.py ../sql/03_mart_views.sql ../sql/03_mart_views_plus_balance.sql

# 5. Build risk package (optional)
cd ../../package_risk
python ../core/python/run_sql.py sql/10_risk_features.sql
python python/train_risk_model.py
python ../core/python/run_sql.py sql/11_risk_score_view.sql

# 6. Build commercial package (optional)
cd ../package_commercial
python ../core/python/run_sql.py sql/20_commercial_marts.sql
```

## Common Queries

### Portfolio Overview

```sql
SELECT
    month_end,
    COUNT(*) AS loans,
    SUM(eop_balance) AS total_balance,
    AVG(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
FROM loan_analytics.mart_portfolio_snapshot_v2
GROUP BY month_end
ORDER BY month_end DESC
LIMIT 12;
```

### Top Risk Loans

```sql
SELECT loan_id, risk_score, eop_balance
FROM loan_analytics.risk_watchlist
ORDER BY risk_score DESC
LIMIT 20;
```

### Product Performance

```sql
SELECT
    p.product_name,
    COUNT(DISTINCT s.loan_id) AS loans,
    AVG(CASE WHEN s.dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
FROM loan_analytics.mart_portfolio_snapshot_v2 s
JOIN loan_analytics.fct_loans l ON s.loan_id = l.loan_id
JOIN loan_analytics.dim_products p ON l.product_id = p.product_id
GROUP BY p.product_name;
```

### Commercial Metrics

```sql
SELECT
    month_end,
    SUM(nii) AS total_nii,
    SUM(rar) AS total_rar
FROM loan_analytics.comm_rar_monthly
GROUP BY month_end
ORDER BY month_end DESC;
```

## Visualization

```bash
# Generate all visualizations (from project root)
python core/python/create_visualizations.py

# Output: visualizations/ folder with PNG charts and optional HTML dashboard
```

## Power BI

1. Connect to your database (SQL Server, MySQL, PostgreSQL, etc.)
2. Import tables from `loan_analytics` schema
3. Copy DAX measures from:
   - `package_risk/powerbi/measures_dax.md`
   - `package_commercial/powerbi/measures_dax.md`

## File Locations

| Item | Location |
|------|----------|
| Schema | `core/sql/01_schema.sql` |
| Baseline marts | `core/sql/03_mart_views.sql` |
| Risk marts | `package_risk/sql/10_risk_features.sql` |
| Commercial marts | `package_commercial/sql/20_commercial_marts.sql` |
| Risk model | `package_risk/python/train_risk_model.py` |
| Visualization script | `core/python/create_visualizations.py` |
| Documentation | `docs/` |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| DB_URL not set (Windows PowerShell) | `$env:DB_URL="sqlite:///loan_demo.db"` |
| DB_URL not set (Windows CMD) | `set DB_URL=sqlite:///loan_demo.db` |
| DB_URL not set (Linux/Mac) | `export DB_URL="sqlite:///loan_demo.db"` |
| Permission denied | Ensure database user has CREATE privileges (SQLite doesn't need this) |
| No data | Run manual setup steps: `python run_pipeline.py` to generate and load data |
| Visualization errors | `pip install -r core/python/requirements.txt` |
