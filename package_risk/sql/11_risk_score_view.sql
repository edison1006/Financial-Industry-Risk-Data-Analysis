-- SQLite-compatible watchlist view
DROP VIEW IF EXISTS risk_watchlist;

-- Output table created by train_risk_model.py: loan_analytics.risk_scores
-- Create a watchlist view for Power BI
CREATE VIEW risk_watchlist AS
SELECT
  s.month_end,
  s.loan_id,
  s.product_type,
  s.channel,
  s.dpd_bucket,
  s.eop_balance,
  r.risk_score
FROM mart_portfolio_snapshot_v2 s
JOIN risk_scores r
  ON r.loan_id = s.loan_id AND r.month_end = s.month_end;
