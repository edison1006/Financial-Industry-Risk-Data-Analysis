# Contributing Guide

Thank you for your interest in contributing to the Financial Industry Risk Data Analysis project!

## Getting Started

1. **Fork the repository**
2. **Clone your fork**:

   ```bash
   git clone https://github.com/your-username/Financial-Industry-Risk-Data-Analysis.git
   cd Financial-Industry-Risk-Data-Analysis
   ```

3. **Set up your environment**:
   - Follow the [Setup Guide](docs/setup_guide.md)
   - Ensure your SQL database is accessible (or use SQLite for testing)
   - Set `DB_URL` environment variable (e.g., `DB_URL="sqlite:///loan_demo.db"`)

4. **Create a branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8 style guide
- **SQL**: Use consistent indentation (2 or 4 spaces)
- **Documentation**: Use Markdown format

### Project Structure

```
├── core/                  # Shared foundation
│   ├── python/            # Data generation and utilities
│   └── sql/               # Schema and baseline marts
├── package_risk/          # Risk & collections package
│   ├── python/            # Risk model training
│   ├── sql/               # Risk marts
│   └── powerbi/           # DAX measures
├── package_commercial/    # Commercial & pricing package
│   ├── sql/               # Commercial marts
│   └── powerbi/           # DAX measures
└── docs/                  # Documentation
```

### Adding New Features

1. **SQL views/marts**:
   - Add to the appropriate package (`package_risk/sql/` or `package_commercial/sql/`)
   - Use numbered prefixes for execution order (e.g. `21_new_mart.sql`)
   - Document in `docs/data_lineage.md`

2. **Python scripts**:
   - Add to the appropriate package directory
   - Include docstrings
   - Handle `DB_URL` environment variable consistently (also accepts `PG_URL` or `DATABASE_URL` for compatibility)

3. **Documentation**:
   - Update relevant docs in `docs/`
   - Add examples if introducing new concepts
   - Update `README.md` if adding major features

### Testing

Before submitting a pull request:

1. **Run the full pipeline**:

   ```bash
   # Follow manual setup steps (see Setup Guide)
   ```

2. **Verify data quality**:
   - Check row counts match expectations
   - Verify calculations are correct
   - Test with sample queries

3. **Test visualizations** (if applicable):

   ```bash
   python core/python/create_visualizations.py
   ```

## Pull Request Process

1. Update documentation for any changes
2. Add comments explaining complex logic
3. Test thoroughly before submitting
4. Write a clear PR description:
   - What changes were made
   - Why they were made
   - How to test them
5. Submit the PR with a descriptive title and link to related issues (if any)

## Reporting Issues

When reporting bugs or requesting features:

1. Check existing issues first
2. Use clear titles and descriptions
3. Include: steps to reproduce, expected vs actual behaviour, environment details, error messages/logs

## Questions?

- Check the [Documentation Index](docs/index.md)
- Review existing code for examples
- Open an issue for discussion

Thank you for contributing!
