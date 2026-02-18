# Documentation Index

## Navigation

| Document | What it covers | Who should read it |
|---|---|---|
| [Architecture](architecture.md) | System design, data flow diagram, technology choices | Everyone (start here) |
| [Data Model](data_model.md) | ER diagram, table relationships, full data dictionary | Analysts, engineers |
| [Data Lineage](data_lineage.md) | Transformation chain from raw to marts, view dependencies | Analysts, engineers |
| [KPI Glossary](kpi_glossary.md) | Formal metric definitions, formulas, interpretation | Everyone |
| [Risk Methodology](methodology_risk.md) | Early-warning model design, features, evaluation | Risk analysts, data scientists |
| [Commercial Methodology](methodology_commercial.md) | NII, expected loss, RAR calculation methodology | Commercial analysts, pricing |
| [Assumptions & Limitations](assumptions_and_limitations.md) | What was simplified and how it affects interpretation | Everyone |
| [Setup Guide](setup_guide.md) | Installation, configuration, Power BI connection | Engineers, new contributors |
| [Database Setup](database_setup.md) | Database connection strings and compatibility notes | Engineers setting up database |
| [Visualization Guide](visualization_guide.md) | Python charts, Power BI dashboards, best practices | Analysts, report builders |
| [Test Data Guide](test_data_guide.md) | Generate test datasets for quick testing | Developers, testers |
| [Quick Reference](quick_reference.md) | Commands, queries, file locations | Everyone |

## Reading Order

**New to this project?** Start with Architecture, then Data Model, then the KPI Glossary.

**Reviewing the analytics?** Read the relevant methodology doc, then the KPI Glossary, then Assumptions.

**Setting up the environment?** Go straight to the Setup Guide.

## Package-Specific References

Each analytical package also has its own lightweight README:

- [Risk / Collections package](../package_risk/README.md) -- quick setup and Power BI measures
- [Commercial / Pricing package](../package_commercial/README.md) -- quick setup and Power BI measures

## Versioning

This documentation corresponds to the current state of the repository. All SQL views, Python models, and Power BI measures referenced in these docs are defined in the source code under `core/`, `package_risk/`, and `package_commercial/`.
