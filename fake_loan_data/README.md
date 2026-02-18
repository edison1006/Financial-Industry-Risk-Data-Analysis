# Sample Data Files

This folder contains sample CSV files and a standard SQL script for quick testing.

## Files

- **`loan_demo.sql`** — Standard SQL script (no PostgreSQL-specific syntax) to create schema and load sample data
- **`dim_customers_sample.csv`** — Sample customer data (10 rows)
- **`fct_loans_sample.csv`** — Sample loan data (10 rows)
- **`fct_payments_sample.csv`** — Sample payment data (30 rows)

## Usage

### Quick Test Setup

If you want to quickly test the database structure without running the full data generation pipeline:

1. Create database: `CREATE DATABASE loan_demo;`
2. Run `loan_demo.sql` in your SQL client (SQL Server, MySQL, PostgreSQL, etc.)
3. This creates the schema and loads sample data

### Full Project Setup

For the complete project with full synthetic data (12,000 loans, 8,000 customers), use the main setup:

```bash
export DB_URL="sqlite:///loan_demo.db"  # Or MySQL, SQL Server, PostgreSQL connection string
# Follow manual setup steps (see docs/setup_guide.md)
```

## Note

These sample files are for testing only. The main project generates comprehensive synthetic data via `core/python/generate_data.py`.
