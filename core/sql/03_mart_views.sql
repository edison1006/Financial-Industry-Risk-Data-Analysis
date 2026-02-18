-- 03_mart_views.sql
-- SQLite-compatible marts (no PostgreSQL-only functions).

DROP VIEW IF EXISTS mart_vintage_60plus;
DROP VIEW IF EXISTS mart_dpd_migration;
DROP VIEW IF EXISTS mart_portfolio_snapshot;
DROP VIEW IF EXISTS mart_loan_dpd_bucket;
DROP VIEW IF EXISTS mart_loan_arrears;
DROP VIEW IF EXISTS mart_loan_due_paid;
DROP VIEW IF EXISTS v_month_ends;

-- Month ends (calendar)
CREATE VIEW v_month_ends AS
WITH RECURSIVE months(m) AS (
  SELECT date('2022-01-01')
  UNION ALL
  SELECT date(m, '+1 month') FROM months WHERE m < date('2026-12-01')
)
SELECT date(m, 'start of month', '+1 month', '-1 day') AS month_end
FROM months;

-- Scheduled vs paid same-month by loan
CREATE VIEW mart_loan_due_paid AS
WITH sch AS (
  SELECT
    loan_id,
    date(due_date, 'start of month', '+1 month', '-1 day') AS due_month_end,
    SUM(scheduled_amount) AS scheduled_amt
  FROM fct_schedule
  GROUP BY 1,2
),
pay AS (
  SELECT
    loan_id,
    date(payment_date, 'start of month', '+1 month', '-1 day') AS pay_month_end,
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
CREATE VIEW mart_loan_arrears AS
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
CREATE VIEW mart_loan_dpd_bucket AS
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
    MAX(0, (arrears_amt * 1.0 / NULLIF(avg_inst,0))) AS missed_inst
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
CREATE VIEW mart_portfolio_snapshot AS
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
CREATE VIEW mart_dpd_migration AS
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
  prev_bucket AS from_bucket,
  dpd_bucket AS to_bucket,
  COUNT(*) AS loan_count
FROM x
WHERE prev_bucket IS NOT NULL
GROUP BY 1,2,3;

-- Vintage 60+ rate by MOB
CREATE VIEW mart_vintage_60plus AS
WITH orig AS (
  SELECT
    loan_id,
    date(origination_date, 'start of month', '+1 month', '-1 day') AS vintage_month
  FROM fct_loans
),
snap AS (
  SELECT loan_id, month_end, dpd_bucket
  FROM mart_loan_dpd_bucket
),
mob AS (
  SELECT
    s.loan_id,
    o.vintage_month,
    s.month_end,
    (
      (CAST(strftime('%Y', s.month_end) AS INTEGER) - CAST(strftime('%Y', o.vintage_month) AS INTEGER)) * 12
      + (CAST(strftime('%m', s.month_end) AS INTEGER) - CAST(strftime('%m', o.vintage_month) AS INTEGER))
    ) AS months_on_books,
    s.dpd_bucket
  FROM snap s
  JOIN orig o ON o.loan_id = s.loan_id
  WHERE s.month_end >= o.vintage_month
)
SELECT
  vintage_month,
  months_on_books,
  COUNT(*) AS loan_cnt,
  SUM(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS bad_60plus_cnt,
  (SUM(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*),0)) AS rate_60plus
FROM mob
GROUP BY 1,2;
