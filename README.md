# Financial Industry Risk Data Analysis

End-to-end analytics platform for a consumer lending portfolio, covering **credit risk monitoring**, **collections prioritisation**, and **commercial profitability analysis**. Built on SQL databases, Python, and Power BI.

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
  subgraph database [SQL Database Warehouse]
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
│   ├── python/            Data generation and SQL execution scripts
│   └── sql/               Schema and mart definitions
├── package_risk/          Risk & collections (delinquency, migration, risk model, watchlist)
│   ├── python/            Risk model training
│   └── sql/               Risk marts and views
├── package_commercial/    Commercial & pricing (interest income, NII, RAR)
│   └── sql/               Commercial marts
└── docs/                  Full documentation suite
```

## Manual Setup

### 1. Set Database Connection

**Windows PowerShell:**
```powershell
# SQLite (simplest, no server needed)
$env:DB_URL="sqlite:///loan_demo.db"

# MySQL
$env:DB_URL="mysql+pymysql://user:password@localhost:3306/loan_demo"

# SQL Server
$env:DB_URL="mssql+pyodbc://user:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server"

# PostgreSQL (if needed)
$env:DB_URL="postgresql://user:password@localhost:5432/loan_demo"
```

**Linux/Mac:**
```bash
# SQLite
export DB_URL="sqlite:///loan_demo.db"

# MySQL
export DB_URL="mysql+pymysql://user:password@localhost:3306/loan_demo"
```

### 2. Install Dependencies

```bash
cd core/python
pip install -r requirements.txt
```

### 3. Create Schema and Tables

```bash
python run_sql.py ../sql/01_schema.sql
```

### 4. Generate and Load Data

```bash
python run_pipeline.py
```

### 5. Build Baseline Marts

```bash
python run_sql.py ../sql/03_mart_views.sql ../sql/03_mart_views_plus_balance.sql
```

### 6. Build Risk Package (Optional)

```bash
cd ../../package_risk
python ../core/python/run_sql.py sql/10_risk_features.sql
python python/train_risk_model.py
python ../core/python/run_sql.py sql/11_risk_score_view.sql
```

### 7. Build Commercial Package (Optional)

```bash
cd ../package_commercial
python ../core/python/run_sql.py sql/20_commercial_marts.sql
```

See the [Setup Guide](docs/setup_guide.md) for detailed manual steps and troubleshooting.

### Utilities

- **Clean generated files**: `.\cleanup.ps1`
- See [CLEANUP.md](CLEANUP.md) for detailed cleanup instructions

### Quick Test Data

For rapid testing and development, use the test data generator:

```powershell
# Generate small test dataset (100 customers, 200 loans)
python core/python/generate_test_data.py --customers 100 --loans 200

# Or load directly to database
python core/python/generate_test_data.py --load-to-db --customers 200 --loans 500
```

See the [Test Data Guide](docs/test_data_guide.md) for more options and examples.

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
| [Database Setup](docs/database_setup.md) | Database connection strings and compatibility notes |
| [Visualization Guide](docs/visualization_guide.md) | Python charts, Power BI dashboards, and best practices |
| [Test Data Guide](docs/test_data_guide.md) | Generate test datasets for quick testing |
| [Quick Reference](docs/quick_reference.md) | Commands, queries, and file locations |
| [Contributing](CONTRIBUTING.md) | How to contribute to the project |

## Key Metrics at a Glance

- **12,000 loans** across 4 product types (Personal, Auto, Mortgage, SME)
- **8,000 customers** with NZ-realistic demographics
- **4-year horizon** (Jan 2022 -- Jan 2026) with full payment histories
- **DPD buckets**: Current, 1-29, 30-59, 60-89, 90+ days past due
- **Risk model**: Logistic regression predicting 60+ DPD within 3 months
- **Commercial view**: Interest income, NII, expected loss, risk-adjusted return

## License

MIT -- see [LICENSE](LICENSE).
