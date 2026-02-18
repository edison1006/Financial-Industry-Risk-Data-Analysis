# Cleanup Guide

This guide helps you clean up generated files and resolve common issues.

## Quick Cleanup

### Remove Generated Files

```powershell
# Run cleanup script
.\cleanup.ps1
```

This removes:
- Generated CSV files in `core/data/raw/`
- Visualization outputs in `visualizations/`
- Python cache files (`__pycache__/`, `*.pyc`)
- Virtual environment (`.venv/`)

**Note:** Sample data in `fake_loan_data/` is kept for reference.

## Reset Database

**WARNING:** This will delete all data in the database!

Use your database client to drop and recreate the database:

**SQLite:**
```powershell
# Simply delete the database file
Remove-Item loan_demo.db
```

**MySQL/SQL Server/PostgreSQL:**
```sql
-- Connect to your database server (not the target database)
-- Run these commands:

DROP DATABASE IF EXISTS loan_demo;
CREATE DATABASE loan_demo;
```

## Manual Cleanup Steps

### 1. Remove Generated CSV Files

```powershell
Remove-Item core\data\raw\*.csv -Force
```

### 2. Remove Visualizations

```powershell
Remove-Item visualizations -Recurse -Force
```

### 3. Remove Python Cache

```powershell
Get-ChildItem -Path . -Include __pycache__,*.pyc -Recurse -Force | Remove-Item -Recurse -Force
```

### 4. Clean Database Schema

If you want to remove all tables/views but keep the database:

**SQL Server/PostgreSQL:**
```sql
-- Connect to loan_demo database
DROP SCHEMA IF EXISTS loan_analytics CASCADE;
CREATE SCHEMA loan_analytics;
```

**SQLite/MySQL:**
```sql
-- Drop all tables manually or recreate database
DROP DATABASE loan_demo;
CREATE DATABASE loan_demo;
```

## Files That Should NOT Be Deleted

These are part of the project and should be kept:

- `fake_loan_data/` - Sample data for reference
- `core/python/` - Python scripts
- `core/sql/` - SQL schema and views
- `package_risk/` - Risk package
- `package_commercial/` - Commercial package
- `docs/` - Documentation
- All `.py`, `.sql`, `.md` files

## Troubleshooting Database Issues

### Connection Errors

**SQLite:** No server needed, just ensure file path is correct.

**MySQL/SQL Server/PostgreSQL:**
- Ensure database server is running
- Check connection string format
- Verify credentials and permissions
- Check firewall settings if connecting remotely
