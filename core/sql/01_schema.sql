-- 01_schema.sql
-- SQLite-first schema (no PostgreSQL-only features).
-- Tables are created WITHOUT a schema prefix to keep SQLite simple.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fct_collections;
DROP TABLE IF EXISTS fct_payments;
DROP TABLE IF EXISTS fct_schedule;
DROP TABLE IF EXISTS fct_loans;
DROP TABLE IF EXISTS dim_channels;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_macro_monthly;

-- Dimension: customers
CREATE TABLE dim_customers (
  customer_id        INTEGER PRIMARY KEY,
  age                INTEGER,
  annual_income_nzd  REAL,
  employment_type    TEXT,
  region             TEXT,
  credit_score       INTEGER,
  tenure_months      INTEGER,
  created_at         TEXT DEFAULT (datetime('now'))
);

-- Dimension: products
CREATE TABLE dim_products (
  product_type       TEXT PRIMARY KEY,   -- Personal, Auto, Mortgage, SME
  secured_flag       INTEGER,            -- 0/1
  base_risk_tier     TEXT
);

-- Dimension: channels
CREATE TABLE dim_channels (
  channel            TEXT PRIMARY KEY,   -- Branch, Broker, Online, Partner
  channel_group      TEXT
);

-- Fact: loans
CREATE TABLE fct_loans (
  loan_id            INTEGER PRIMARY KEY,
  customer_id        INTEGER NOT NULL REFERENCES dim_customers(customer_id),
  product_type       TEXT NOT NULL,
  origination_date   TEXT NOT NULL,      -- ISO date string YYYY-MM-DD
  principal_nzd      REAL NOT NULL,
  interest_rate_apr  REAL NOT NULL,
  term_months        INTEGER NOT NULL,
  channel            TEXT NOT NULL,
  status             TEXT DEFAULT 'Active',
  created_at         TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_loans_customer ON fct_loans(customer_id);
CREATE INDEX idx_loans_origdate ON fct_loans(origination_date);

-- Fact: schedule
CREATE TABLE fct_schedule (
  schedule_id         INTEGER PRIMARY KEY AUTOINCREMENT,
  loan_id             INTEGER NOT NULL REFERENCES fct_loans(loan_id),
  installment_no      INTEGER NOT NULL,
  due_date            TEXT NOT NULL,     -- ISO date string YYYY-MM-DD
  scheduled_amount    REAL NOT NULL,
  scheduled_principal REAL NOT NULL,
  scheduled_interest  REAL NOT NULL
);

CREATE INDEX idx_schedule_loan_due ON fct_schedule(loan_id, due_date);

-- Fact: payments
CREATE TABLE fct_payments (
  payment_id         INTEGER PRIMARY KEY AUTOINCREMENT,
  loan_id            INTEGER NOT NULL REFERENCES fct_loans(loan_id),
  payment_date       TEXT NOT NULL,      -- ISO date string YYYY-MM-DD
  paid_amount        REAL NOT NULL
);

CREATE INDEX idx_payments_loan_date ON fct_payments(loan_id, payment_date);

-- Optional: collections
CREATE TABLE fct_collections (
  collection_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  loan_id             INTEGER NOT NULL REFERENCES fct_loans(loan_id),
  event_date          TEXT NOT NULL,
  action_type         TEXT,
  promised_to_pay_date TEXT
);

CREATE INDEX idx_collections_loan_date ON fct_collections(loan_id, event_date);

-- Optional: macro monthly
CREATE TABLE dim_macro_monthly (
  month              TEXT PRIMARY KEY,   -- month start YYYY-MM-01
  unemployment_rate  REAL,
  cpi_index          REAL,
  cash_rate          REAL
);
