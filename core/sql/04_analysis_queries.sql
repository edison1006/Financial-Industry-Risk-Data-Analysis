-- 04_analysis_queries.sql
SET search_path TO loan_analytics;

-- Monthly 30+/60+/90+ rates
SELECT
  month_end,
  COUNT(*) AS loans,
  AVG(CASE WHEN dpd_bucket IN ('DPD_30_59','DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_30p,
  AVG(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p,
  AVG(CASE WHEN dpd_bucket = 'DPD_90_PLUS' THEN 1 ELSE 0 END) AS rate_90p
FROM mart_portfolio_snapshot_v2
GROUP BY 1
ORDER BY 1;

-- Worst segments (latest month)
WITH latest AS (SELECT MAX(month_end) AS month_end FROM mart_portfolio_snapshot_v2)
SELECT
  s.month_end,
  s.channel,
  s.product_type,
  COUNT(*) AS loans,
  AVG(CASE WHEN s.dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS bad_60p_rate
FROM mart_portfolio_snapshot_v2 s
JOIN latest l ON l.month_end = s.month_end
GROUP BY 1,2,3
HAVING COUNT(*) >= 200
ORDER BY bad_60p_rate DESC;

-- Migration matrix sample
SELECT *
FROM mart_dpd_migration
WHERE month_end = '2025-12-31'
ORDER BY prev_bucket, curr_bucket;

-- Vintage curve sample
SELECT *
FROM mart_vintage_60plus
WHERE orig_month_end BETWEEN '2023-01-31' AND '2024-12-31'
ORDER BY orig_month_end, months_on_book;
