# Database Setup Guide

This project uses standard SQL and SQLAlchemy, supporting multiple database engines.

## Supported Databases

- **SQLite** (simplest, no server needed)
- **MySQL** / **MariaDB**
- **SQL Server**
- **PostgreSQL**
- Any database supported by SQLAlchemy

## Connection String Format

Set the `DB_URL` environment variable with your database connection string:

### SQLite (Recommended for Testing)

```powershell
# Windows PowerShell
$env:DB_URL="sqlite:///loan_demo.db"

# Linux/Mac
export DB_URL="sqlite:///loan_demo.db"
```

**Note:** SQLite doesn't support schemas. The SQL files use `loan_analytics.` schema prefix which SQLite will ignore.

### MySQL

```powershell
# Windows PowerShell
$env:DB_URL="mysql+pymysql://username:password@localhost:3306/loan_demo"

# Linux/Mac
export DB_URL="mysql+pymysql://username:password@localhost:3306/loan_demo"
```

**Required package:** `pip install pymysql`

**Note:** MySQL uses databases instead of schemas. Create database `loan_demo` first, then the schema prefix will work.

### SQL Server

```powershell
# Windows PowerShell
$env:DB_URL="mssql+pyodbc://username:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server"

# Linux/Mac
export DB_URL="mssql+pyodbc://username:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server"
```

**Required package:** `pip install pyodbc`

### PostgreSQL

```powershell
# Windows PowerShell
$env:DB_URL="postgresql://username:password@localhost:5432/loan_demo"

# Linux/Mac
export DB_URL="postgresql://username:password@localhost:5432/loan_demo"
```

**Required package:** `pip install psycopg2-binary` (optional, only if using PostgreSQL)

## Database-Specific Notes

### SQLite

- No server installation needed
- Database file created automatically
- Schema prefix (`loan_analytics.`) is ignored
- Best for testing and development

### MySQL

- Create database first: `CREATE DATABASE loan_demo;`
- May need to adjust `IDENTITY(1,1)` to `AUTO_INCREMENT` in SQL files
- Schema support depends on MySQL version

### SQL Server

- Uses `IDENTITY(1,1)` for auto-increment (already in SQL files)
- Full schema support
- May need ODBC driver installed

### PostgreSQL

- Create database first: `CREATE DATABASE loan_demo;`
- Full schema support
- May need to adjust `IDENTITY(1,1)` to `SERIAL` or `BIGSERIAL` in SQL files

## SQL File Compatibility

The SQL files in this project use standard SQL where possible, but some database-specific syntax may need adjustment:

| Feature | Standard SQL | SQLite | MySQL | SQL Server | PostgreSQL |
|---------|-------------|--------|-------|------------|------------|
| Auto-increment | `IDENTITY(1,1)` | `AUTOINCREMENT` | `AUTO_INCREMENT` | `IDENTITY(1,1)` | `SERIAL` |
| Schema | `CREATE SCHEMA` | Ignored | Database | Supported | Supported |
| Boolean | `BIT` | `INTEGER` | `TINYINT(1)` | `BIT` | `BOOLEAN` |
| Date functions | Varies | Limited | Varies | Varies | Varies |

**Note:** Some SQL files (especially `03_mart_views.sql`) contain database-specific functions. You may need to adjust date functions and window functions for your specific database.

## Quick Start with SQLite

The simplest way to get started:

```powershell
# 1. Set SQLite connection
$env:DB_URL="sqlite:///loan_demo.db"

# 2. Install dependencies
cd core/python
pip install -r requirements.txt

# 3. Create schema (SQLite will ignore schema prefix)
python run_sql.py ../sql/01_schema.sql

# 4. Generate and load data
python run_pipeline.py

# 5. Build marts (may need adjustment for SQLite date functions)
python run_sql.py ../sql/03_mart_views.sql
```

## Troubleshooting

**Error: "No module named 'pymysql'"**
- Install MySQL driver: `pip install pymysql`

**Error: "No module named 'pyodbc'"**
- Install SQL Server driver: `pip install pyodbc`

**Error: "Schema does not exist"**
- SQLite: Ignore schema prefix, tables will be created in default namespace
- MySQL: Create database first: `CREATE DATABASE loan_demo;`
- SQL Server/PostgreSQL: Schema will be created automatically

**Error: "IDENTITY not supported"**
- MySQL: Replace `IDENTITY(1,1)` with `AUTO_INCREMENT`
- PostgreSQL: Replace with `SERIAL` or `BIGSERIAL`
