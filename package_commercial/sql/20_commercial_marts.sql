-- SQLite-compatible commercial marts
DROP VIEW IF EXISTS comm_rar_monthly;
DROP VIEW IF EXISTS comm_nii_monthly;
DROP VIEW IF EXISTS comm_interest_income_monthly;

-- 1) Interest income estimate (proxy): EOP balance * APR / 12
CREATE VIEW comm_interest_income_monthly AS
SELECT
  s.month_end,
  s.loan_id,
  s.product_type,
  s.channel,
  s.principal_nzd AS eop_balance, -- proxy to avoid expensive balance view
  s.interest_rate_apr,
  ROUND((s.principal_nzd * s.interest_rate_apr / 12.0), 2) AS interest_income_est
FROM mart_portfolio_snapshot s;

-- 2) Funding cost + NII estimate (proxy)
CREATE VIEW comm_nii_monthly AS
WITH base AS (
  SELECT
    month_end, loan_id, product_type, channel,
    principal_nzd AS eop_balance, interest_rate_apr,
    (principal_nzd * interest_rate_apr / 12.0) AS int_income,
    (principal_nzd * 0.055 / 12.0) AS funding_cost  -- assume 5.5% annual funding cost
  FROM mart_portfolio_snapshot
)
SELECT
  month_end, loan_id, product_type, channel,
  eop_balance,
  ROUND(int_income, 2) AS interest_income_est,
  ROUND(funding_cost, 2) AS funding_cost_est,
  ROUND((int_income - funding_cost), 2) AS nii_est
FROM base;

-- 3) Risk-adjusted return (RAR proxy): NII - Expected Loss
CREATE VIEW comm_rar_monthly AS
WITH pd_map AS (
  SELECT
    loan_id, month_end,
    CASE
      WHEN dpd_bucket='DPD_0' THEN 0.01
      WHEN dpd_bucket='DPD_1_29' THEN 0.03
      WHEN dpd_bucket='DPD_30_59' THEN 0.10
      WHEN dpd_bucket='DPD_60_89' THEN 0.30
      ELSE 0.55
    END AS pd_proxy
  FROM mart_portfolio_snapshot
),
base AS (
  SELECT
    n.month_end, n.loan_id, s.product_type, s.channel,
    n.eop_balance,
    n.nii_est,
    p.pd_proxy,
    0.55 AS lgd_assumption
  FROM comm_nii_monthly n
  JOIN mart_portfolio_snapshot s ON s.loan_id=n.loan_id AND s.month_end=n.month_end
  JOIN pd_map p ON p.loan_id=n.loan_id AND p.month_end=n.month_end
)
SELECT
  month_end, loan_id, product_type, channel, eop_balance,
  nii_est,
  ROUND((eop_balance * pd_proxy * lgd_assumption), 2) AS expected_loss_est,
  ROUND((nii_est - (eop_balance * pd_proxy * lgd_assumption)), 2) AS rar_profit_est
FROM base;
