-- 03_mart_views.sql
CREATE SCHEMA IF NOT EXISTS loan_analytics;
SET search_path TO loan_analytics;

-- Month ends
CREATE OR REPLACE VIEW v_month_ends AS
SELECT (date_trunc('month', dd)::date + interval '1 month - 1 day')::date AS month_end
FROM generate_series('2022-01-01'::date, '2026-12-31'::date, interval '1 month') dd;

-- Scheduled vs paid same-month by loan
CREATE OR REPLACE VIEW mart_loan_due_paid AS
WITH sch AS (
  SELECT
    loan_id,
    (date_trunc('month', due_date)::date + interval '1 month - 1 day')::date AS due_month_end,
    SUM(scheduled_amount) AS scheduled_amt
  FROM fct_schedule
  GROUP BY 1,2
),
pay AS (
  SELECT
    loan_id,
    (date_trunc('month', payment_date)::date + interval '1 month - 1 day')::date AS pay_month_end,
    SUM(paid_amount) AS paid_amt
  FROM fct_payments
  GROUP BY 1,2
)
SELECT
  s.loan_id,
  s.due_month_end,
  s.scheduled_amt,
  COALESCE(p.paid_amt, 0) AS paid_amt_same_month
FROM sch s
LEFT JOIN pay p
  ON p.loan_id = s.loan_id
 AND p.pay_month_end = s.due_month_end;

-- Cumulative arrears
CREATE OR REPLACE VIEW mart_loan_arrears AS
WITH base AS (
  SELECT
    loan_id,
    due_month_end AS month_end,
    scheduled_amt,
    paid_amt_same_month
  FROM mart_loan_due_paid
),
cum AS (
  SELECT
    loan_id,
    month_end,
    scheduled_amt,
    paid_amt_same_month,
    SUM(scheduled_amt) OVER (PARTITION BY loan_id ORDER BY month_end) AS cum_scheduled,
    SUM(paid_amt_same_month) OVER (PARTITION BY loan_id ORDER BY month_end) AS cum_paid
  FROM base
)
SELECT
  loan_id,
  month_end,
  scheduled_amt,
  paid_amt_same_month,
  (cum_scheduled - cum_paid) AS arrears_amt
FROM cum;

-- DPD bucket approximation via missed-installments proxy
CREATE OR REPLACE VIEW mart_loan_dpd_bucket AS
WITH s AS (
  SELECT loan_id, AVG(scheduled_amount) AS avg_inst
  FROM fct_schedule
  GROUP BY 1
),
a AS (
  SELECT
    ar.loan_id,
    ar.month_end,
    ar.arrears_amt,
    COALESCE(s.avg_inst, 1) AS avg_inst
  FROM mart_loan_arrears ar
  LEFT JOIN s ON s.loan_id = ar.loan_id
),
b AS (
  SELECT
    loan_id,
    month_end,
    arrears_amt,
    GREATEST(0, (arrears_amt / NULLIF(avg_inst,0))) AS missed_inst
  FROM a
)
SELECT
  loan_id,
  month_end,
  arrears_amt,
  missed_inst,
  CASE
    WHEN arrears_amt <= 0 THEN 'DPD_0'
    WHEN missed_inst < 1.0 THEN 'DPD_1_29'
    WHEN missed_inst < 2.0 THEN 'DPD_30_59'
    WHEN missed_inst < 3.0 THEN 'DPD_60_89'
    ELSE 'DPD_90_PLUS'
  END AS dpd_bucket
FROM b;

-- Portfolio snapshot v1
CREATE OR REPLACE VIEW mart_portfolio_snapshot AS
SELECT
  b.month_end,
  l.loan_id,
  l.customer_id,
  l.product_type,
  l.channel,
  l.origination_date,
  l.principal_nzd,
  l.interest_rate_apr,
  l.term_months,
  b.arrears_amt,
  b.dpd_bucket
FROM mart_loan_dpd_bucket b
JOIN fct_loans l
  ON l.loan_id = b.loan_id;

-- Migration matrix
CREATE OR REPLACE VIEW mart_dpd_migration AS
WITH x AS (
  SELECT
    loan_id,
    month_end,
    dpd_bucket,
    LAG(dpd_bucket) OVER (PARTITION BY loan_id ORDER BY month_end) AS prev_bucket
  FROM mart_loan_dpd_bucket
)
SELECT
  month_end,
  prev_bucket,
  dpd_bucket AS curr_bucket,
  COUNT(*) AS loan_count
FROM x
WHERE prev_bucket IS NOT NULL
GROUP BY 1,2,3;

-- Vintage 60+ rate by MOB
CREATE OR REPLACE VIEW mart_vintage_60plus AS
WITH orig AS (
  SELECT
    loan_id,
    (date_trunc('month', origination_date)::date + interval '1 month - 1 day')::date AS orig_month_end
  FROM fct_loans
),
snap AS (
  SELECT loan_id, month_end, dpd_bucket
  FROM mart_loan_dpd_bucket
),
mob AS (
  SELECT
    s.loan_id,
    o.orig_month_end,
    s.month_end,
    ( (date_part('year', s.month_end) - date_part('year', o.orig_month_end)) * 12
      + (date_part('month', s.month_end) - date_part('month', o.orig_month_end)) )::int AS months_on_book,
    s.dpd_bucket
  FROM snap s
  JOIN orig o ON o.loan_id = s.loan_id
  WHERE s.month_end >= o.orig_month_end
)
SELECT
  orig_month_end,
  months_on_book,
  COUNT(*) AS loan_cnt,
  SUM(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS bad_60p_cnt,
  (SUM(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*),0)) AS bad_60p_rate
FROM mob
GROUP BY 1,2;
