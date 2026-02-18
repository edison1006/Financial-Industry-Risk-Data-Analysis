# Risk Scoring Methodology

## Business Objective

Identify loans likely to enter **60+ days past due (DPD) within the next 3 months**, enabling the collections team to intervene early. The model produces a continuous risk score (0 to 1) that feeds a prioritised watchlist ranked by score and balance.

## Problem Framing

| Aspect | Decision |
|---|---|
| Task | Binary classification |
| Target variable | `will_be_60p_in_3m`: 1 if the loan enters DPD_60_89 or DPD_90_PLUS in any of the next 3 months, 0 otherwise |
| Prediction horizon | 3 months forward |
| Observation grain | Loan x month (each loan-month is one training observation) |
| Output | Predicted probability (risk_score) per loan-month |

### Why 60+ DPD and 3 Months?

- **60+ DPD** is the standard materiality threshold in consumer lending -- loans at this stage have historically low cure rates and require active collections.
- **3 months** provides enough lead time for the collections team to act (contact, hardship referral, payment plan) before the loan reaches 90+ DPD (non-performing).

## Feature Engineering

Features are computed in the SQL view `risk_features_3m` and combine static borrower attributes with dynamic behavioural signals.

### Static Features (from origination)

| Feature | Source | Rationale |
|---|---|---|
| credit_score | dim_customers | Primary indicator of creditworthiness at onboarding |
| annual_income_nzd | dim_customers | Capacity to service debt |
| employment_type | dim_customers | Stability of income source (categorical) |
| product_type | fct_loans | Different products carry different inherent risk profiles |
| channel | fct_loans | Origination channel correlates with underwriting quality |
| interest_rate_apr | fct_loans | Higher rates signal higher-risk pricing at origination |

### Dynamic Features (rolling 3-month window)

| Feature | Source | Rationale |
|---|---|---|
| roll3_paid_full_rate | risk_pay_behaviour_monthly | Proportion of the last 3 months where the borrower paid the full scheduled amount; direct measure of payment discipline |
| roll3_missed_cnt | risk_pay_behaviour_monthly | Count of months with underpayment in the last 3 months; captures deterioration velocity |
| roll3_avg_arrears | mart_portfolio_snapshot_v2 | Average arrears amount over the last 3 months; captures severity of shortfall |
| eop_balance | mart_portfolio_snapshot_v2 | Current exposure; higher balance = higher loss-given-default |
| dpd_bucket | mart_portfolio_snapshot_v2 | Current delinquency status (categorical); strongest single predictor |

### Label Construction

The label `will_be_60p_in_3m` is built in `risk_labels_60p_3m` using a forward-looking window:

```sql
MAX(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END)
  OVER (PARTITION BY loan_id ORDER BY month_end
        ROWS BETWEEN 1 FOLLOWING AND 3 FOLLOWING)
```

This means: for each loan-month, look ahead 1-3 months and flag 1 if the loan appears in 60+ DPD in any of those future months.

## Model Design

### Algorithm: Logistic Regression

| Choice | Rationale |
|---|---|
| Logistic regression | Interpretable coefficients, fast to train, well-understood in credit risk |
| Class weighting | `class_weight="balanced"` compensates for imbalanced classes (most loans are performing) |
| Max iterations | 300 (sufficient for convergence on this dataset) |
| Regularisation | Default L2 (C=1.0) to prevent overfitting |

### Preprocessing Pipeline

```
ColumnTransformer
├── Numeric features → passthrough (no scaling needed for logistic regression with L2)
└── Categorical features → OneHotEncoder (handle_unknown="ignore")
```

### Train / Test Split

- **75% train, 25% test** with stratified sampling on the target variable
- Random state = 42 for reproducibility
- Rows with null rolling features (insufficient history) are excluded

## Evaluation Metrics

| Metric | Purpose |
|---|---|
| **AUC (ROC)** | Overall discrimination ability; insensitive to threshold choice |
| **Precision** | Of loans flagged as high-risk, how many actually deteriorated? (controls false positives = wasted collections effort) |
| **Recall** | Of loans that actually deteriorated, how many did we catch? (controls false negatives = missed interventions) |
| **F1** | Harmonic mean of precision and recall; balanced summary |

The model is evaluated at the default threshold of 0.5 for precision/recall/F1, but in practice the watchlist uses continuous scores ranked by descending probability.

## Scoring and Consumption

After training, the full dataset (all loan-months) is scored:

```python
df["risk_score"] = pipe.predict_proba(X)[:, 1]
```

Scores are written to `loan_analytics.risk_scores` and consumed via the `risk_watchlist` view, which joins scores with the portfolio snapshot for Power BI dashboards.

### Watchlist Prioritisation

Collections teams rank by:
1. **risk_score** (descending) -- highest probability of deterioration
2. **eop_balance** (descending) -- highest potential loss

This dual ranking ensures effort is focused on both the most likely and the most costly defaults.

## Limitations and Future Improvements

| Limitation | Impact | Potential Improvement |
|---|---|---|
| Logistic regression assumes linear decision boundary | May underfit complex interactions between features | Gradient boosting (XGBoost, LightGBM) for non-linear patterns |
| No macroeconomic features | Model cannot anticipate systemic deterioration (recession, rate hikes) | Incorporate `dim_macro_monthly` (unemployment, CPI, cash rate) |
| No time-series cross-validation | Train/test split does not respect temporal ordering | Expanding-window or walk-forward validation to avoid data leakage |
| Synthetic data | Delinquency patterns are simulated, not observed | Validate on real portfolio data before production deployment |
| Single threshold (0.5) | May not be optimal for business cost structure | Calibrate threshold using collections capacity and cost-of-miss vs cost-of-false-alarm |
| No model monitoring | Score drift not tracked over time | Implement PSI (Population Stability Index) and model performance tracking |
