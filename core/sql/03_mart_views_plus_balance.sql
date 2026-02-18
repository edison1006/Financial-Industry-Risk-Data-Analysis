-- 03_mart_views_plus_balance.sql
SET search_path TO loan_analytics;

-- Monthly principal repaid from schedule (proxy)
CREATE OR REPLACE VIEW mart_principal_paid_by_month AS
SELECT
  loan_id,
  (date_trunc('month', due_date)::date + interval '1 month - 1 day')::date AS month_end,
  SUM(scheduled_principal) AS sched_principal
FROM fct_schedule
GROUP BY 1,2;

-- EOP balance = orig principal - cumulative scheduled principal (clamped)
CREATE OR REPLACE VIEW mart_balance_eop AS
WITH p AS (
  SELECT
    l.loan_id,
    l.principal_nzd,
    m.month_end,
    COALESCE(pp.sched_principal, 0) AS sched_principal
  FROM fct_loans l
  JOIN (SELECT DISTINCT month_end FROM mart_loan_dpd_bucket) m ON 1=1
  LEFT JOIN mart_principal_paid_by_month pp
    ON pp.loan_id = l.loan_id AND pp.month_end = m.month_end
  WHERE m.month_end >= (date_trunc('month', l.origination_date)::date + interval '1 month - 1 day')::date
),
cum AS (
  SELECT
    loan_id,
    month_end,
    principal_nzd,
    SUM(sched_principal) OVER (PARTITION BY loan_id ORDER BY month_end) AS cum_principal
  FROM p
)
SELECT
  loan_id,
  month_end,
  GREATEST(0, (principal_nzd - cum_principal))::numeric(14,2) AS eop_balance
FROM cum;

-- Upgraded snapshot v2 (use this for Power BI)
CREATE OR REPLACE VIEW mart_portfolio_snapshot_v2 AS
SELECT
  s.month_end,
  s.loan_id,
  s.customer_id,
  s.product_type,
  s.channel,
  s.origination_date,
  s.principal_nzd,
  s.interest_rate_apr,
  s.term_months,
  s.arrears_amt,
  s.dpd_bucket,
  b.eop_balance
FROM mart_portfolio_snapshot s
LEFT JOIN mart_balance_eop b
  ON b.loan_id = s.loan_id AND b.month_end = s.month_end;
