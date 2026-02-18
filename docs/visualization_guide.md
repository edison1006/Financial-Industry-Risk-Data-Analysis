# Data Visualization Guide

This guide covers how to create visualizations for the Financial Industry Risk Data Analysis project using both Python and Power BI.

## Table of Contents

1. [Python Visualizations](#python-visualizations)
2. [Power BI Dashboards](#power-bi-dashboards)
3. [Visualization Best Practices](#visualization-best-practices)
4. [Common Visualizations](#common-visualizations)

## Python Visualizations

### Prerequisites

Install visualization libraries:

```bash
cd core/python
pip install -r requirements.txt
```

This installs:

- `matplotlib` — Static charts
- `seaborn` — Statistical visualizations
- `plotly` — Interactive charts (optional for HTML dashboard)

### Quick Start

1. Set your database connection:

   ```bash
   # SQLite (simplest)
   export DB_URL="sqlite:///loan_demo.db"
   
   # MySQL
   export DB_URL="mysql+pymysql://user:password@localhost:3306/loan_demo"
   ```

2. Run the visualization script (from project root):

   ```bash
   python core/python/create_visualizations.py
   ```

This generates:

- **Static PNG charts** in the `visualizations/` folder:
  - `delinquency_trends.png` — Delinquency rates over time
  - `dpd_by_product.png` — DPD distribution by product
  - `migration_matrix.png` — DPD migration heatmap
  - `vintage_analysis.png` — Vintage curves
  - `risk_scores.png` — Risk score distribution
  - `commercial_metrics.png` — NII and RAR trends

- **Interactive HTML dashboard** (if plotly is installed):
  - `interactive_dashboard.html` — Open in a browser for interactive exploration

### Custom Visualizations

You can create custom visualizations by querying the database marts directly:

```python
import os
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

db_url = os.getenv("DB_URL") or os.getenv("PG_URL") or os.getenv("DATABASE_URL")
engine = create_engine(db_url)

query = """
SELECT month_end, COUNT(*) AS loans
FROM loan_analytics.mart_portfolio_snapshot_v2
GROUP BY month_end
ORDER BY month_end;
"""
df = pd.read_sql_query(query, engine)

plt.figure(figsize=(12, 6))
plt.plot(df["month_end"], df["loans"])
plt.title("Portfolio Size Over Time")
plt.xlabel("Month End")
plt.ylabel("Number of Loans")
plt.savefig("custom_chart.png")
plt.close()

conn.close()
```

## Power BI Dashboards

### Connection Setup

1. Open Power BI Desktop
2. Get Data → Select your database type (SQL Server, MySQL, PostgreSQL, etc.)
3. Enter connection details (server, database, credentials)
4. Choose **DirectQuery** (for live data) or **Import** (for faster performance)

### Recommended Tables

| View | Purpose |
|------|---------|
| `loan_analytics.mart_portfolio_snapshot_v2` | Primary fact table (loan × month with DPD and balance) |
| `loan_analytics.mart_dpd_migration` | Migration matrix data |
| `loan_analytics.mart_vintage_60plus` | Vintage analysis data |
| `loan_analytics.risk_watchlist` | Scored watchlist for collections |
| `loan_analytics.comm_interest_income_monthly` | Interest income estimates |
| `loan_analytics.comm_nii_monthly` | NII estimates |
| `loan_analytics.comm_rar_monthly` | Risk-adjusted return estimates |

### DAX Measures

Import DAX measures from:

- `package_risk/powerbi/measures_dax.md` — Risk/delinquency measures
- `package_commercial/powerbi/measures_dax.md` — Commercial/profitability measures

Copy and paste these measures into Power BI’s “New Measure” dialog.

### Suggested Dashboard Pages

| Page | Key Visuals | Primary View |
|------|-------------|--------------|
| Portfolio Overview | Loan count trend, EOP balance trend, DPD distribution | mart_portfolio_snapshot_v2 |
| Delinquency Deep-Dive | Rate 30+/60+/90+ over time, by product, by channel | mart_portfolio_snapshot_v2 |
| Migration Matrix | Heatmap of bucket transitions | mart_dpd_migration |
| Vintage Analysis | Line chart of 60+ rate by MOB, coloured by vintage | mart_vintage_60plus |
| Risk Watchlist | Table of top-risk loans, risk score distribution | risk_watchlist |
| Commercial / Profitability | NII and RAR by product and channel, margin trends | comm_rar_monthly |

## Visualization Best Practices

### Color Schemes

- **Delinquency**: Use red/yellow/green gradient (red = worse)
- **Profitability**: Use green/blue (green = better)
- **Risk scores**: Use continuous colour scale (red = high risk)

### Chart Types

| Metric | Recommended Chart Type |
|--------|-------------------------|
| Trends over time | Line chart |
| Distribution | Histogram or box plot |
| Comparisons | Bar chart (horizontal for many categories) |
| Relationships | Scatter plot |
| Migration | Heatmap |
| Composition | Stacked bar or pie chart |

### Labels and Titles

Always include:

- Clear, descriptive titles
- Axis labels with units
- Legend for multi-series charts
- Data source and date range

## Common Visualizations

### 1. Delinquency Rate Trend

**Purpose**: Monitor portfolio health over time.

**Query**:

```sql
SELECT
    month_end,
    AVG(CASE WHEN dpd_bucket IN ('DPD_60_89', 'DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
FROM loan_analytics.mart_portfolio_snapshot_v2
GROUP BY month_end
ORDER BY month_end;
```

**Visualization**: Line chart with `month_end` on x-axis, `rate_60p` on y-axis.

### 2. Product Performance Comparison

**Purpose**: Compare delinquency rates across products.

**Query**:

```sql
SELECT
    p.product_name,
    AVG(CASE WHEN s.dpd_bucket IN ('DPD_60_89', 'DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
FROM loan_analytics.mart_portfolio_snapshot_v2 s
JOIN loan_analytics.fct_loans l ON s.loan_id = l.loan_id
JOIN loan_analytics.dim_products p ON l.product_id = p.product_id
GROUP BY p.product_name;
```

**Visualization**: Horizontal bar chart sorted by `rate_60p`.

### 3. Risk Score vs Balance

**Purpose**: Identify high-risk, high-balance loans for collections prioritisation.

**Query**:

```sql
SELECT risk_score, eop_balance
FROM loan_analytics.risk_watchlist
WHERE risk_score IS NOT NULL;
```

**Visualization**: Scatter plot with `risk_score` on x-axis, `eop_balance` on y-axis.

## Troubleshooting

### Python Visualizations

- **Error: "Missing database connection"** — Set the environment variable: `export DB_URL="sqlite:///loan_demo.db"`
- **Error: "No module named 'matplotlib'"** — Install dependencies: `pip install -r requirements.txt`
- **Charts look blurry** — Increase DPI: `plt.savefig('chart.png', dpi=300)`

### Power BI

- **Slow performance** — Switch from DirectQuery to Import mode, or reduce date range.
- **Measures return errors** — Check table and column names match your schema; verify relationships.

## Additional Resources

- [Matplotlib Documentation](https://matplotlib.org/)
- [Seaborn Documentation](https://seaborn.pydata.org/)
- [Plotly Documentation](https://plotly.com/python/)
- [Power BI DAX Guide](https://docs.microsoft.com/en-us/dax/)
