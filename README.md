# Financial Industry Risk Data Analysis

End-to-end analytics platform for a consumer lending portfolio, covering **credit risk monitoring**, **collections prioritisation**, and **commercial profitability analysis**. Built on PostgreSQL, Python, and Power BI.

The project answers questions every lending stakeholder asks:

| Stakeholder | Question | Package |
|---|---|---|
| Credit Risk | How is delinquency trending? Which segments are deteriorating? | Core + Risk |
| Collections | Which loans need attention first? What is the roll-rate pattern? | Risk |
| Commercial / Pricing | Are we earning enough margin after risk? Which channels deliver ROI? | Commercial |
| Portfolio Management | What does the vintage curve look like? Is origination quality stable? | Core |

## Architecture

```mermaid
flowchart LR
  subgraph generation [Data Generation]
    GenPy[generate_data.py]
  end
  subgraph postgres [PostgreSQL Data Warehouse]
    Raw[Raw Tables] --> BaseMarts[Baseline Marts]
    BaseMarts --> RiskMarts[Risk Marts]
    BaseMarts --> CommMarts[Commercial Marts]
  end
  subgraph analytics [Analytics Layer]
    RiskModel[Risk Model]
    PowerBI[Power BI Dashboards]
  end
  GenPy -->|CSV| Raw
  RiskMarts --> RiskModel -->|Scores| RiskMarts
  BaseMarts --> PowerBI
  RiskMarts --> PowerBI
  CommMarts --> PowerBI
```

## Repository Structure

```
├── core/                  Shared foundation (schema, data generation, baseline marts)
├── package_risk/          Risk & collections (delinquency, migration, risk model, watchlist)
├── package_commercial/    Commercial & pricing (interest income, NII, RAR)
├── docs/                  Full documentation suite
├── run_all.py             One-command orchestration
└── run_all.sh             Shell wrapper
```

## Quick Start

```bash
# 1. Set your PostgreSQL connection
export PG_URL="postgresql://user:password@localhost:5432/loan_demo"

# 2. Run everything (schema + data + marts + model)
python run_all.py
```

See the [Setup Guide](docs/setup_guide.md) for prerequisites, manual steps, and troubleshooting.

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design, data flow, and technology rationale |
| [Data Model](docs/data_model.md) | Entity-relationship diagram and full data dictionary |
| [Data Lineage](docs/data_lineage.md) | Transformation chain from raw tables to analytical marts |
| [KPI Glossary](docs/kpi_glossary.md) | Formal definitions for every business metric |
| [Risk Methodology](docs/methodology_risk.md) | Early-warning model design, features, and evaluation |
| [Commercial Methodology](docs/methodology_commercial.md) | NII, expected loss, and risk-adjusted return calculations |
| [Assumptions & Limitations](docs/assumptions_and_limitations.md) | What was simplified and why |
| [Setup Guide](docs/setup_guide.md) | Full installation, configuration, and Power BI setup |

## Key Metrics at a Glance

- **12,000 loans** across 4 product types (Personal, Auto, Mortgage, SME)
- **8,000 customers** with NZ-realistic demographics
- **4-year horizon** (Jan 2022 -- Jan 2026) with full payment histories
- **DPD buckets**: Current, 1-29, 30-59, 60-89, 90+ days past due
- **Risk model**: Logistic regression predicting 60+ DPD within 3 months
- **Commercial view**: Interest income, NII, expected loss, risk-adjusted return

## License

MIT -- see [LICENSE](LICENSE).
