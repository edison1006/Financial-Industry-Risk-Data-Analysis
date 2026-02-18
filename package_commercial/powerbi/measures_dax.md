# Commercial / Pricing Measures (DAX)

EOP Balance = SUM(mart_portfolio_snapshot_v2[eop_balance])

Interest Income (est) = SUM(comm_interest_income_monthly[interest_income_est])
Funding Cost (est) = SUM(comm_nii_monthly[funding_cost_est])
NII (est) = SUM(comm_nii_monthly[nii_est])

Expected Loss (est) = SUM(comm_rar_monthly[expected_loss_est])
RAR Profit (est) = SUM(comm_rar_monthly[rar_profit_est])

NII Margin = DIVIDE([NII (est)], [EOP Balance])
RAR Margin = DIVIDE([RAR Profit (est)], [EOP Balance])

-- Risk context (reuse delinquency buckets)
Loans = COUNTROWS(mart_portfolio_snapshot_v2)
Loans 60+ =
CALCULATE(
    [Loans],
    mart_portfolio_snapshot_v2[dpd_bucket] IN {"DPD_60_89","DPD_90_PLUS"}
)
Rate 60+ = DIVIDE([Loans 60+], [Loans])
