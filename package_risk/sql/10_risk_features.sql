SET search_path TO loan_analytics;

-- Payment behaviour by month (paid vs scheduled)
CREATE OR REPLACE VIEW risk_pay_behaviour_monthly AS
WITH due AS (
  SELECT loan_id, due_month_end AS month_end, scheduled_amt
  FROM mart_loan_due_paid
),
paid AS (
  SELECT loan_id, due_month_end AS month_end, paid_amt_same_month AS paid_amt
  FROM mart_loan_due_paid
)
SELECT
  d.loan_id,
  d.month_end,
  d.scheduled_amt,
  p.paid_amt,
  CASE WHEN p.paid_amt >= d.scheduled_amt THEN 1 ELSE 0 END AS paid_full_flag
FROM due d
JOIN paid p USING (loan_id, month_end);

-- Rolling 3M features
CREATE OR REPLACE VIEW risk_features_3m AS
WITH x AS (
  SELECT
    s.loan_id,
    s.month_end,
    s.dpd_bucket,
    s.arrears_amt,
    s.eop_balance,
    l.product_type,
    l.channel,
    l.interest_rate_apr,
    c.credit_score,
    c.annual_income_nzd,
    c.employment_type,
    AVG(b.paid_full_flag::numeric) OVER (PARTITION BY s.loan_id ORDER BY s.month_end ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS roll3_paid_full_rate,
    SUM(CASE WHEN b.paid_full_flag=0 THEN 1 ELSE 0 END) OVER (PARTITION BY s.loan_id ORDER BY s.month_end ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS roll3_missed_cnt,
    AVG(s.arrears_amt) OVER (PARTITION BY s.loan_id ORDER BY s.month_end ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS roll3_avg_arrears
  FROM mart_portfolio_snapshot_v2 s
  JOIN fct_loans l ON l.loan_id = s.loan_id
  JOIN dim_customers c ON c.customer_id = l.customer_id
  LEFT JOIN risk_pay_behaviour_monthly b
    ON b.loan_id = s.loan_id AND b.month_end = s.month_end
)
SELECT * FROM x;

-- Label: will enter 60+ within next 3 months
CREATE OR REPLACE VIEW risk_labels_60p_3m AS
WITH base AS (
  SELECT loan_id, month_end, dpd_bucket
  FROM mart_portfolio_snapshot_v2
),
fwd AS (
  SELECT
    loan_id,
    month_end,
    MAX(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END)
      OVER (PARTITION BY loan_id ORDER BY month_end ROWS BETWEEN 1 FOLLOWING AND 3 FOLLOWING) AS will_be_60p_in_3m
  FROM base
)
SELECT loan_id, month_end, COALESCE(will_be_60p_in_3m,0) AS will_be_60p_in_3m
FROM fwd;
