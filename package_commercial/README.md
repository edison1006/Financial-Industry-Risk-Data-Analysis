# Package B — Commercial / Pricing

## What this package delivers
- Monthly interest income estimate (proxy) and funding cost estimate
- NII estimate and risk-adjusted profit (RAR proxy = NII - Expected Loss)
- Segment profitability by **product** and **channel**
- Pricing effectiveness: APR vs risk vs risk-adjusted margin

## Setup
1) Run core steps first (schema, data generation, load, baseline marts, plus balance):
- `core/sql/01_schema_postgres.sql`
- `core/sql/03_mart_views.sql`
- `core/sql/03_mart_views_plus_balance.sql`

2) Create commercial marts:
- `package_commercial/sql/20_commercial_marts.sql`

## Power BI
Import:
- `loan_analytics.mart_portfolio_snapshot_v2`
- `loan_analytics.comm_interest_income_monthly`
- `loan_analytics.comm_nii_monthly`
- `loan_analytics.comm_rar_monthly`

Paste measures from `powerbi/measures_dax.md`.

## Story / Recommendations
- Compare channel ROI (volume vs quality vs RAR margin).
- Identify segments where higher APR correlates with worse risk (adverse selection).
- Suggest pricing bands and channel mix adjustments to improve risk-adjusted returns.
