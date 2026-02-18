# Test Data Generation Guide

This guide explains how to generate test data for quick testing and development of the Financial Risk Analysis model.

## Quick Test Data Generator

The project includes a simplified test data generator (`core/python/generate_test_data.py`) that creates smaller, configurable datasets for rapid iteration.

### Features

- **Configurable size**: Generate 50-1000 customers/loans (vs. full 8,000/12,000)
- **Fast generation**: Creates test data in seconds
- **Realistic patterns**: Includes risk-based payment behavior
- **Direct database loading**: Option to load directly to database
- **Reproducible**: Uses random seeds for consistent results

## Usage

### Basic Usage (Generate CSV Files)

```bash
# Generate default test data (100 customers, 200 loans)
python core/python/generate_test_data.py

# Custom size
python core/python/generate_test_data.py --customers 50 --loans 100

# Custom output directory
python core/python/generate_test_data.py --output-dir ./test_data

# Different random seed
python core/python/generate_test_data.py --seed 123
```

### Direct Database Loading

```bash
# Set database connection
$env:DB_URL="sqlite:///loan_demo.db"  # Simplest option

# Or for other databases:
$env:DB_URL="mysql+pymysql://user:password@localhost:3306/loan_demo"
$env:DB_URL="postgresql://user:password@localhost:5432/loan_demo"

# Generate and load directly to database
python core/python/generate_test_data.py --load-to-db --customers 200 --loans 500
```

**Note**: This requires the database schema to already exist. Run `python core/python/run_sql.py core/sql/01_schema.sql` first to create the schema, or use the SQL script in `fake_loan_data/loan_demo.sql`.

### Command-Line Options

| Option | Description | Default |
|-------|-------------|---------|
| `--customers` | Number of customers to generate | 100 |
| `--loans` | Number of loans to generate | 200 |
| `--seed` | Random seed for reproducibility | 42 |
| `--output-dir` | Directory for CSV output | `../data/raw` |
| `--load-to-db` | Load directly to database | False |

## Test Data Characteristics

The test data generator creates realistic synthetic data with:

### Customers
- **Demographics**: Age, income, employment type, region (NZ-based)
- **Credit profiles**: Credit scores (450-850), tenure
- **Distribution**: Realistic distributions matching NZ population

### Loans
- **Products**: Personal, Auto, Mortgage, SME (configurable mix)
- **Channels**: Online, Branch, Broker, Partner
- **Terms**: 12-300 months depending on product
- **Amounts**: $2,000 - $1,200,000 (product-dependent)
- **Rates**: Realistic APR ranges per product type

### Payment Behavior
- **Risk-based**: Payment probability based on:
  - Credit score
  - Income level
  - Employment type
  - Product risk tier
  - Channel risk multiplier
  - Interest rate
- **Delinquency patterns**: Late payments, missed payments, partial payments
- **Collections events**: SMS, calls, emails, agent contacts

## Example Workflows

### Quick Test (50 customers, 100 loans)

```bash
# Generate small test dataset
python core/python/generate_test_data.py --customers 50 --loans 100

# Load to database (if schema exists)
python core/python/load_data.py

# Build marts
python core/python/run_sql.py ../sql/03_mart_views.sql

# Test visualizations
python core/python/create_visualizations.py
```

### Development Testing (200 customers, 500 loans)

```bash
# Generate and load directly
python core/python/generate_test_data.py --load-to-db --customers 200 --loans 500

# Build marts
python core/python/run_sql.py ../sql/03_mart_views.sql ../sql/03_mart_views_plus_balance.sql

# Train risk model
python package_risk/python/train_risk_model.py
```

### Full Dataset (Production-like)

For the full dataset (8,000 customers, 12,000 loans), use the main generator:

```bash
python core/python/generate_data.py
python core/python/load_data.py
# Follow manual setup steps (see Setup Guide)
```

## Comparing Test vs Full Data

| Aspect | Test Data | Full Data |
|--------|-----------|-----------|
| Customers | 50-1,000 | 8,000 |
| Loans | 100-2,000 | 12,000 |
| Schedule rows | ~5,000-100,000 | ~500,000 |
| Payment rows | ~4,000-80,000 | ~400,000 |
| Generation time | < 5 seconds | ~30-60 seconds |
| Use case | Quick testing, development | Full analysis, demos |

## Tips

1. **Start small**: Use 50-100 customers for initial testing
2. **Increase gradually**: Scale up as you test different scenarios
3. **Use seeds**: Same seed = same data (useful for debugging)
4. **Test edge cases**: Generate data with specific characteristics:
   - High-risk customers (low credit scores)
   - Long-term loans (mortgages)
   - Short-term loans (personal loans)

## Troubleshooting

**Error: "Missing database connection"**
- Set environment variable: `$env:DB_URL="sqlite:///loan_demo.db"`

**Error: "Schema does not exist"**
- Create schema first: `python core/python/run_sql.py core/sql/01_schema.sql` or run `fake_loan_data/loan_demo.sql`

**Error: "Table already has data"**
- Clear tables first or use `--load-to-db` which appends data
- To replace: `TRUNCATE TABLE loan_analytics.fct_loans CASCADE;`

**Data looks unrealistic**
- Adjust seed: `--seed 999` for different patterns
- Increase sample size for better distributions

## Next Steps

After generating test data:
1. Load to database (if using CSV)
2. Build marts: `python core/python/run_sql.py ../sql/03_mart_views.sql`
3. Test queries from [Quick Reference](quick_reference.md)
4. Generate visualizations: `python core/python/create_visualizations.py`
5. Train risk model: `python package_risk/python/train_risk_model.py`
