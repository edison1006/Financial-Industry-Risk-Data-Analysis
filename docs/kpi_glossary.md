# KPI Glossary

This document is the single source of truth for all business metrics used in dashboards, reports, and analytical queries. Power BI DAX measures (in `package_risk/powerbi/measures_dax.md` and `package_commercial/powerbi/measures_dax.md`) implement these definitions.

## Portfolio Health Metrics

| Metric | Formula | Unit | Grain | Interpretation |
|---|---|---|---|---|
| **Loan Count** | `COUNT(loan_id)` from snapshot | Count | Month | Total active loans in the portfolio at month-end |
| **EOP Balance** | `SUM(eop_balance)` | NZD | Month | Total outstanding principal at end of period; the portfolio's exposure |
| **DPD Bucket** | Arrears-based classification (see below) | Category | Loan x month | Risk status of each loan: DPD_0, DPD_1_29, DPD_30_59, DPD_60_89, DPD_90_PLUS |
| **Rate 30+** | Loans in 30-59 / 60-89 / 90+ divided by total loans | % | Month | Early stress indicator; loans past first missed installment |
| **Rate 60+** | Loans in 60-89 / 90+ divided by total loans | % | Month | Material delinquency; standard watchlist threshold |
| **NPL Rate (90+)** | Loans in 90+ divided by total loans | % | Month | Non-performing loan rate; regulatory reporting threshold |
| **EOP 60+ Balance** | `SUM(eop_balance)` for loans with dpd_bucket in (DPD_60_89, DPD_90_PLUS) | NZD | Month | Balance-weighted delinquency exposure |
| **EOP 60+ Rate** | EOP 60+ Balance / EOP Balance | % | Month | Share of outstanding balance that is materially delinquent |

### DPD Bucket Logic

DPD (days past due) is approximated using a missed-installment proxy rather than actual calendar days:

```
missed_installments = MAX(0, cumulative_arrears / average_installment_amount)

DPD_0:        arrears <= 0
DPD_1_29:     0 < missed_installments < 1
DPD_30_59:    1 <= missed_installments < 2
DPD_60_89:    2 <= missed_installments < 3
DPD_90_PLUS:  missed_installments >= 3
```

**Source view:** `mart_loan_dpd_bucket`

## Risk Metrics

| Metric | Formula | Unit | Grain | Interpretation |
|---|---|---|---|---|
| **Migration Rate** | Loan count transitioning from bucket A to bucket B / total loans in bucket A | % | Month x bucket pair | Probability of a loan worsening (or curing) between consecutive months |
| **Roll Rate** | Specifically, migration from one bucket to the next-worse bucket | % | Month x bucket | Forward flow rate; key input for loss forecasting |
| **Vintage 60+ Rate** | Loans that reached 60+ DPD / total loans in origination cohort, by months-on-book | % | Vintage x MOB | Origination quality indicator; steeper curves signal worse underwriting |
| **Risk Score** | Predicted probability of entering 60+ DPD within 3 months (logistic regression) | 0.0 -- 1.0 | Loan x month | Higher = more likely to deteriorate; used for collections prioritisation |
| **Avg Risk Score** | `AVERAGE(risk_score)` across portfolio or segment | 0.0 -- 1.0 | Month or segment | Overall risk temperature of a portfolio slice |
| **Top Risk Balance** | `SUM(eop_balance)` for the top 100 loans ranked by risk_score descending | NZD | Month | Concentrated risk exposure in highest-risk loans |

### Migration Matrix

The migration matrix tracks how loans move between DPD buckets from one month to the next:

```
              ┌──────────────────────────────── Current Month ──────────────────────────────┐
              │  DPD_0    DPD_1_29    DPD_30_59    DPD_60_89    DPD_90_PLUS                 │
Previous Month│                                                                             │
DPD_0         │  Stay     Worsen      Worsen       Worsen       Worsen                      │
DPD_1_29      │  Cure     Stay        Roll         Roll         Roll                        │
DPD_30_59     │  Cure     Cure        Stay         Roll         Roll                        │
DPD_60_89     │  Cure     Cure        Cure         Stay         Roll                        │
DPD_90_PLUS   │  Cure     Cure        Cure         Cure         Stay                        │
└─────────────┴─────────────────────────────────────────────────────────────────────────────┘
```

**Source view:** `mart_dpd_migration`

## Commercial Metrics

| Metric | Formula | Unit | Grain | Interpretation |
|---|---|---|---|---|
| **Interest Income (est)** | EOP Balance x APR / 12 | NZD | Loan x month | Monthly revenue proxy from interest charges |
| **Funding Cost (est)** | EOP Balance x 5.5% / 12 | NZD | Loan x month | Cost of funds proxy (flat annual rate assumption) |
| **NII (est)** | Interest Income - Funding Cost | NZD | Loan x month | Net interest income; the spread earned on each loan |
| **NII Margin** | NII / EOP Balance | % | Month or segment | Profitability of the interest spread relative to exposure |
| **Expected Loss (est)** | EOP Balance x PD proxy x LGD (55%) | NZD | Loan x month | Anticipated credit loss based on current delinquency status |
| **RAR Profit (est)** | NII - Expected Loss | NZD | Loan x month | Risk-adjusted return; margin after accounting for expected credit losses |
| **RAR Margin** | RAR Profit / EOP Balance | % | Month or segment | Risk-adjusted profitability relative to exposure; the key pricing effectiveness metric |

### PD Proxy Mapping

Since this is a portfolio monitoring tool (not a regulatory model), PD is approximated from DPD status:

| DPD Bucket | PD Proxy | Rationale |
|---|---|---|
| DPD_0 | 1% | Performing; baseline default rate |
| DPD_1_29 | 3% | Minor arrears; elevated but recoverable |
| DPD_30_59 | 10% | Missed one full installment; material risk |
| DPD_60_89 | 30% | Missed two installments; high risk |
| DPD_90_PLUS | 55% | Non-performing; majority expected to default |

**LGD assumption:** 55% (blended across secured and unsecured products).

**Source view:** `comm_rar_monthly`
