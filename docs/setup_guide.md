# Setup Guide

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10 or higher | Data generation, loading, model training |
| SQL Database | Any SQLAlchemy-supported database | Data warehouse (SQLite, MySQL, SQL Server, PostgreSQL, etc.) |
| pip | Latest | Python package management |
| Power BI Desktop | Latest (optional) | Dashboard visualisation |

Verify your environment:

```bash
python --version    # should be 3.10+
```

## 1. Database Setup

This project supports multiple database engines. Choose one:

### Option A: SQLite (Simplest - No Server Needed)

No setup required! SQLite creates a file-based database automatically.

```powershell
# Windows PowerShell
$env:DB_URL="sqlite:///loan_demo.db"
```

```bash
# Linux/Mac
export DB_URL="sqlite:///loan_demo.db"
```

### Option B: MySQL

1. Install MySQL server
2. Create database:
   ```sql
   CREATE DATABASE loan_demo;
   ```
3. Set connection:
   ```powershell
   $env:DB_URL="mysql+pymysql://username:password@localhost:3306/loan_demo"
   ```
4. Install driver: `pip install pymysql`

### Option C: SQL Server

1. Install SQL Server
2. Create database:
   ```sql
   CREATE DATABASE loan_demo;
   ```
3. Set connection:
   ```powershell
   $env:DB_URL="mssql+pyodbc://username:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server"
   ```
4. Install driver: `pip install pyodbc`

### Option D: PostgreSQL

1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE loan_demo;
   ```
3. Set connection:
   ```powershell
   $env:DB_URL="postgresql://username:password@localhost:5432/loan_demo"
   ```
4. Install driver: `pip install psycopg2-binary` (optional)

See [Database Setup Guide](database_setup.md) for detailed instructions for each database type.

## 2. Set the Connection String

All scripts read the database connection from the `DB_URL` environment variable (also accepts `PG_URL` or `DATABASE_URL` for compatibility):

**Windows PowerShell:**
```powershell
# SQLite (recommended for testing)
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
export DB_URL="mysql+pymysql://username:password@localhost:3306/loan_demo"
```

Replace `username` and `password` with your database credentials.

**Note:** On Windows, environment variables set this way only persist for the current session. To make it permanent:
- Add to your PowerShell profile: `$env:DB_URL = "sqlite:///loan_demo.db"`
- Or use System Properties → Environment Variables (permanent for all sessions)

## 3. Manual Setup Steps

Follow these steps manually to set up the platform:

### Step 1: Install Dependencies

```bash
cd core/python
pip install -r requirements.txt
```

### Step 2: Create Schema and Tables

```bash
python run_sql.py ../sql/01_schema.sql
```

### Step 3: Generate Data and Load to PostgreSQL

```bash
python run_pipeline.py
```

This generates synthetic data (CSV) and loads it into your database.

### Step 4: Build Baseline Marts

```bash
python run_sql.py ../sql/03_mart_views.sql ../sql/03_mart_views_plus_balance.sql
```

### Step 5: Build Risk Package (Optional)

```bash
cd ../../package_risk
python ../core/python/run_sql.py sql/10_risk_features.sql
python python/train_risk_model.py
python ../core/python/run_sql.py sql/11_risk_score_view.sql
```

### Step 6: Build Commercial Package (Optional)

```bash
cd ../package_commercial
python ../core/python/run_sql.py sql/20_commercial_marts.sql
```

## 4. Verify the Setup

After completing the manual setup steps, verify with these queries:

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
python run_sql.py ../sql/01_schema.sql
```

### Step 3: Generate data and load into database

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

### Connect to Database

1. Open Power BI Desktop
2. Get Data -> Select your database type:
   - **SQL Server database** (for SQL Server)
   - **MySQL database** (for MySQL)
   - **PostgreSQL database** (for PostgreSQL)
   - **SQLite database** (for SQLite - may need ODBC driver)
3. Enter connection details (server, database, credentials)
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

### DB_URL not set

**Symptom:** `Missing database connection` error

**Fix:** Set the DB_URL environment variable before running:

```powershell
# Windows PowerShell
$env:DB_URL="sqlite:///loan_demo.db"  # Simplest option

# Or for other databases:
$env:DB_URL="mysql+pymysql://user:password@localhost:3306/loan_demo"
```

```bash
# Linux/Mac
export DB_URL="sqlite:///loan_demo.db"
```

### Database driver not found

**Symptom:** `No module named 'pymysql'` or similar

**Fix:** Install the appropriate database driver:

```bash
# For MySQL
pip install pymysql

# For SQL Server
pip install pyodbc

# For PostgreSQL (optional)
pip install psycopg2-binary
```

### Permission denied on schema

**Symptom:** `permission denied for schema loan_analytics`

**Fix:** Ensure your database user has CREATE privileges. For SQLite, this is not an issue.

### Views return zero rows

**Symptom:** Mart views exist but return no data

**Fix:** Ensure data was loaded. Check:

```sql
SELECT COUNT(*) FROM loan_analytics.fct_loans;
```

If zero, re-run `python run_pipeline.py` from `core/python/`.

### SQL syntax errors

**Symptom:** SQL execution fails with syntax errors

**Fix:** Some SQL files contain database-specific functions. You may need to adjust:
- Date functions (`date_trunc`, `generate_series` in PostgreSQL)
- Window functions syntax
- Auto-increment syntax (`IDENTITY` vs `AUTO_INCREMENT` vs `SERIAL`)

See [Database Setup Guide](database_setup.md) for database-specific notes.
