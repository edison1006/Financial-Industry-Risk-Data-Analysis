-- 01_schema_postgres.sql
-- Tested for PostgreSQL 13+

CREATE SCHEMA IF NOT EXISTS loan_analytics;
SET search_path TO loan_analytics;

-- Dimension: customers
CREATE TABLE IF NOT EXISTS dim_customers (
  customer_id        BIGINT PRIMARY KEY,
  age                INT,
  annual_income_nzd  NUMERIC(12,2),
  employment_type    TEXT,
  region             TEXT,
  credit_score       INT,
  tenure_months      INT,
  created_at         TIMESTAMP DEFAULT now()
);

-- Dimension: products
CREATE TABLE IF NOT EXISTS dim_products (
  product_type       TEXT PRIMARY KEY,   -- Personal, Auto, Mortgage, SME
  secured_flag       BOOLEAN,
  base_risk_tier     TEXT
);

-- Dimension: channels
CREATE TABLE IF NOT EXISTS dim_channels (
  channel            TEXT PRIMARY KEY,   -- Branch, Broker, Online, Partner
  channel_group      TEXT
);

-- Fact: loans
CREATE TABLE IF NOT EXISTS fct_loans (
  loan_id            BIGINT PRIMARY KEY,
  customer_id        BIGINT NOT NULL REFERENCES dim_customers(customer_id),
  product_type       TEXT NOT NULL,
  origination_date   DATE NOT NULL,
  principal_nzd      NUMERIC(14,2) NOT NULL,
  interest_rate_apr  NUMERIC(6,4) NOT NULL,
  term_months        INT NOT NULL,
  channel            TEXT NOT NULL,
  status             TEXT DEFAULT 'Active',
  created_at         TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_loans_customer ON fct_loans(customer_id);
CREATE INDEX IF NOT EXISTS idx_loans_origdate ON fct_loans(origination_date);

-- Fact: schedule
CREATE TABLE IF NOT EXISTS fct_schedule (
  schedule_id        BIGSERIAL PRIMARY KEY,
  loan_id            BIGINT NOT NULL REFERENCES fct_loans(loan_id),
  installment_no     INT NOT NULL,
  due_date           DATE NOT NULL,
  scheduled_amount   NUMERIC(14,2) NOT NULL,
  scheduled_principal NUMERIC(14,2) NOT NULL,
  scheduled_interest  NUMERIC(14,2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_schedule_loan_due ON fct_schedule(loan_id, due_date);

-- Fact: payments
CREATE TABLE IF NOT EXISTS fct_payments (
  payment_id         BIGSERIAL PRIMARY KEY,
  loan_id            BIGINT NOT NULL REFERENCES fct_loans(loan_id),
  payment_date       DATE NOT NULL,
  paid_amount        NUMERIC(14,2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payments_loan_date ON fct_payments(loan_id, payment_date);

-- Optional: collections
CREATE TABLE IF NOT EXISTS fct_collections (
  collection_id      BIGSERIAL PRIMARY KEY,
  loan_id            BIGINT NOT NULL REFERENCES fct_loans(loan_id),
  event_date         DATE NOT NULL,
  action_type        TEXT,
  promised_to_pay_date DATE
);

CREATE INDEX IF NOT EXISTS idx_collections_loan_date ON fct_collections(loan_id, event_date);

-- Optional: macro monthly
CREATE TABLE IF NOT EXISTS dim_macro_monthly (
  month              DATE PRIMARY KEY,    -- month start
  unemployment_rate  NUMERIC(6,4),
  cpi_index          NUMERIC(10,4),
  cash_rate          NUMERIC(6,4)
);
