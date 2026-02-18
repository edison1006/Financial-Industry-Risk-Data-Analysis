# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Python visualization script (`core/python/create_visualizations.py`)
- Visualization guide (`docs/visualization_guide.md`)
- Quick reference guide (`docs/quick_reference.md`)
- Database setup guide (`docs/database_setup.md`)
- Contributing guide (`CONTRIBUTING.md`)
- Changelog (`CHANGELOG.md`)
- Support for matplotlib, seaborn, and plotly in `requirements.txt`
- Test data generator (`core/python/generate_test_data.py`)
- Cleanup utilities (`cleanup.ps1`)

### Changed

- **BREAKING:** Removed all PostgreSQL-specific dependencies and code
- **BREAKING:** Changed from `PG_URL` to `DB_URL` environment variable (still accepts `PG_URL` for compatibility)
- **BREAKING:** Removed all automated startup scripts (`run_all.py`, `run_core.py`, `run_risk.py`, `run_commercial.py`)
- Updated `core/python/requirements.txt` to remove `psycopg2-binary`
- Renamed `01_schema_postgres.sql` to `01_schema.sql` (standard SQL)
- Renamed `load_to_postgres.py` to `load_data.py` (generic database loader)
- Updated all Python scripts to use SQLAlchemy for database-agnostic connections
- Updated all documentation to support multiple database engines (SQLite, MySQL, SQL Server, PostgreSQL)
- All SQL files now use standard SQL syntax (may need database-specific adjustments)

## [1.0.0] - 2026-02-18

### Added

- Initial release
- Core data generation and loading pipeline
- SQL schema and baseline marts (originally PostgreSQL-specific, now database-agnostic)
- Risk package (delinquency monitoring, migration matrix, early-warning model)
- Commercial package (NII, RAR calculations)
- Power BI DAX measures
- Documentation suite (architecture, data model, lineage, KPI glossary, methodologies, setup)

### Features

- Synthetic loan portfolio data generation (12,000 loans, 8,000 customers)
- DPD bucketing and migration analysis
- Vintage analysis
- Risk scoring model (logistic regression)
- Commercial profitability analysis
- Power BI dashboard templates
