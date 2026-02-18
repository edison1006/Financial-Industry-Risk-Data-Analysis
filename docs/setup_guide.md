# Setup Guide

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10 or higher | Data generation, loading, model training |
| PostgreSQL | 13 or higher | Data warehouse |
| pip | Latest | Python package management |
| Power BI Desktop | Latest (optional) | Dashboard visualisation |

Verify your environment:

```bash
python --version    # should be 3.10+
psql --version      # should be 13+
```

## 1. Database Setup

Create a PostgreSQL database for the project:

```bash
createdb loan_demo
```

Or via psql:

```sql
CREATE DATABASE loan_demo;
```

## 2. Set the Connection String

All scripts read the database connection from the `PG_URL` environment variable:

```bash
export PG_URL="postgresql://username:password@localhost:5432/loan_demo"
```

Replace `username` and `password` with your PostgreSQL credentials. Add this to your shell profile (`.zshrc` or `.bashrc`) to persist across sessions.

## 3. Run Everything (Recommended)

The simplest way to set up the entire platform:

```bash
python run_all.py
```

This executes the following in order:

1. Installs Python dependencies (`core/python/requirements.txt`)
2. Creates the `loan_analytics` schema and all tables
3. Generates synthetic data (CSV) and loads it into PostgreSQL
4. Builds baseline marts (DPD, migration, vintage, EOP balance)
5. Builds risk features and trains the early-warning model
6. Creates the risk watchlist view
7. Builds commercial marts (interest income, NII, RAR)

Alternatively, use the shell wrapper:

```bash
chmod +x run_all.sh
./run_all.sh
```

## 4. Verify the Setup

After `run_all.py` completes, verify with these queries:

```sql
-- Check row counts
SELECT COUNT(*) FROM loan_analytics.fct_loans;           -- ~12,000
SELECT COUNT(*) FROM loan_analytics.fct_payments;         -- ~400,000+

-- Check baseline mart
SELECT * FROM loan_analytics.mart_portfolio_snapshot_v2 LIMIT 10;

-- Check risk watchlist
SELECT * FROM loan_analytics.risk_watchlist LIMIT 10;

-- Check commercial mart
SELECT * FROM loan_analytics.comm_rar_monthly LIMIT 10;

-- Monthly delinquency summary
SELECT month_end, COUNT(*) AS loans,
       AVG(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
FROM loan_analytics.mart_portfolio_snapshot_v2
GROUP BY 1
ORDER BY 1;
```

## 5. Manual Step-by-Step Run (Optional)

If you prefer to run each stage individually:

### Step 1: Install dependencies

```bash
cd core/python
pip install -r requirements.txt
```

### Step 2: Create schema and tables

```bash
python run_sql.py ../sql/01_schema_postgres.sql
```

### Step 3: Generate data and load into PostgreSQL

```bash
python run_pipeline.py
```

### Step 4: Build baseline marts

```bash
python run_sql.py ../sql/03_mart_views.sql ../sql/03_mart_views_plus_balance.sql
```

### Step 5: Build risk package (optional)

```bash
cd ../../package_risk
python ../core/python/run_sql.py sql/10_risk_features.sql
python python/train_risk_model.py
python ../core/python/run_sql.py sql/11_risk_score_view.sql
```

### Step 6: Build commercial package (optional)

```bash
cd ../package_commercial
python ../core/python/run_sql.py sql/20_commercial_marts.sql
```

## 6. Power BI Connection

### Connect to PostgreSQL

1. Open Power BI Desktop
2. Get Data -> PostgreSQL database
3. Server: `localhost` (or your host), Database: `loan_demo`
4. Choose **DirectQuery** or **Import** mode

### Recommended Tables to Import

| View | Package | Purpose |
|---|---|---|
| `loan_analytics.mart_portfolio_snapshot_v2` | Core | Primary fact table (loan x month with DPD and balance) |
| `loan_analytics.mart_dpd_migration` | Core | Migration matrix data |
| `loan_analytics.mart_vintage_60plus` | Core | Vintage analysis data |
| `loan_analytics.risk_watchlist` | Risk | Scored watchlist for collections |
| `loan_analytics.comm_interest_income_monthly` | Commercial | Interest income estimates |
| `loan_analytics.comm_nii_monthly` | Commercial | NII estimates |
| `loan_analytics.comm_rar_monthly` | Commercial | Risk-adjusted return estimates |

### Add DAX Measures

Paste measures from:
- `package_risk/powerbi/measures_dax.md` for risk/delinquency measures
- `package_commercial/powerbi/measures_dax.md` for commercial/profitability measures

### Suggested Dashboard Pages

| Page | Key Visuals | Primary View |
|---|---|---|
| Portfolio Overview | Loan count trend, EOP balance trend, DPD distribution | mart_portfolio_snapshot_v2 |
| Delinquency Deep-Dive | Rate 30+/60+/90+ over time, by product, by channel | mart_portfolio_snapshot_v2 |
| Migration Matrix | Heatmap of bucket transitions | mart_dpd_migration |
| Vintage Analysis | Line chart of 60+ rate by MOB, coloured by vintage | mart_vintage_60plus |
| Risk Watchlist | Table of top-risk loans, risk score distribution | risk_watchlist |
| Commercial / Profitability | NII and RAR by product and channel, margin trends | comm_rar_monthly |

## Troubleshooting

### psycopg2-binary fails to build

**Symptom:** `error: failed-wheel-build-install` when installing `psycopg2-binary`

**Cause:** No pre-built wheel for your Python version (common with Python 3.13+)

**Fix:** The project uses `psycopg2-binary>=2.9.10` which supports Python 3.13. If you still see the error, try:

```bash
pip install --upgrade pip
pip install psycopg2-binary
```

Or install the non-binary version (requires PostgreSQL development headers):

```bash
brew install postgresql    # macOS
pip install psycopg2
```

### PG_URL not set

**Symptom:** `Missing PG_URL` error

**Fix:** Set the environment variable before running:

```bash
export PG_URL="postgresql://user:password@localhost:5432/loan_demo"
```

### Permission denied on schema

**Symptom:** `permission denied for schema loan_analytics`

**Fix:** Ensure your PostgreSQL user has CREATE privileges:

```sql
GRANT ALL ON DATABASE loan_demo TO your_user;
```

### Views return zero rows

**Symptom:** Mart views exist but return no data

**Fix:** Ensure data was loaded. Check:

```sql
SELECT COUNT(*) FROM loan_analytics.fct_loans;
```

If zero, re-run `python run_pipeline.py` from `core/python/`.
