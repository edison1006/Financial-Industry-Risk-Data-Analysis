# Risk Measures (DAX)

## Core counts & rates
Loans = COUNTROWS(mart_portfolio_snapshot_v2)

Loans 30+ =
CALCULATE(
    [Loans],
    mart_portfolio_snapshot_v2[dpd_bucket] IN {"DPD_30_59","DPD_60_89","DPD_90_PLUS"}
)

Loans 60+ =
CALCULATE(
    [Loans],
    mart_portfolio_snapshot_v2[dpd_bucket] IN {"DPD_60_89","DPD_90_PLUS"}
)

Loans 90+ =
CALCULATE(
    [Loans],
    mart_portfolio_snapshot_v2[dpd_bucket] = "DPD_90_PLUS"
)

Rate 30+ = DIVIDE([Loans 30+], [Loans])
Rate 60+ = DIVIDE([Loans 60+], [Loans])
NPL (90+) Rate = DIVIDE([Loans 90+], [Loans])

## Balance-weighted rates
EOP Balance = SUM(mart_portfolio_snapshot_v2[eop_balance])

EOP 60+ Balance =
CALCULATE(
  [EOP Balance],
  mart_portfolio_snapshot_v2[dpd_bucket] IN {"DPD_60_89","DPD_90_PLUS"}
)

EOP 60+ Rate = DIVIDE([EOP 60+ Balance], [EOP Balance])

## Watchlist (risk_scores / risk_watchlist)
Avg Risk Score = AVERAGE(risk_watchlist[risk_score])

Top Risk Balance (sum) =
CALCULATE([EOP Balance], TOPN(100, risk_watchlist, risk_watchlist[risk_score], DESC))
