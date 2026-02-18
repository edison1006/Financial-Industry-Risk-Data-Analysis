SET search_path TO loan_analytics;

-- 1) Interest income estimate (proxy): EOP balance * APR / 12
CREATE OR REPLACE VIEW comm_interest_income_monthly AS
SELECT
  s.month_end,
  s.loan_id,
  s.product_type,
  s.channel,
  s.eop_balance,
  s.interest_rate_apr,
  (s.eop_balance * s.interest_rate_apr / 12.0)::numeric(14,2) AS interest_income_est
FROM mart_portfolio_snapshot_v2 s;

-- 2) Funding cost + NII estimate (proxy)
CREATE OR REPLACE VIEW comm_nii_monthly AS
WITH base AS (
  SELECT
    month_end, loan_id, product_type, channel,
    eop_balance, interest_rate_apr,
    (eop_balance * interest_rate_apr / 12.0) AS int_income,
    (eop_balance * 0.055 / 12.0) AS funding_cost  -- assume 5.5% annual funding cost
  FROM mart_portfolio_snapshot_v2
)
SELECT
  month_end, loan_id, product_type, channel,
  eop_balance,
  int_income::numeric(14,2) AS interest_income_est,
  funding_cost::numeric(14,2) AS funding_cost_est,
  (int_income - funding_cost)::numeric(14,2) AS nii_est
FROM base;

-- 3) Risk-adjusted return (RAR proxy): NII - Expected Loss
CREATE OR REPLACE VIEW comm_rar_monthly AS
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
  FROM mart_portfolio_snapshot_v2
),
base AS (
  SELECT
    n.month_end, n.loan_id, s.product_type, s.channel,
    s.eop_balance,
    n.nii_est,
    p.pd_proxy,
    0.55 AS lgd_assumption
  FROM comm_nii_monthly n
  JOIN mart_portfolio_snapshot_v2 s ON s.loan_id=n.loan_id AND s.month_end=n.month_end
  JOIN pd_map p ON p.loan_id=n.loan_id AND p.month_end=n.month_end
)
SELECT
  month_end, loan_id, product_type, channel, eop_balance,
  nii_est,
  (eop_balance * pd_proxy * lgd_assumption)::numeric(14,2) AS expected_loss_est,
  (nii_est - (eop_balance * pd_proxy * lgd_assumption))::numeric(14,2) AS rar_profit_est
FROM base;
