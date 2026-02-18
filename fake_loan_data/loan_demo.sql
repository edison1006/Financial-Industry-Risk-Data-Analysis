-- loan_demo.sql
-- Standard SQL (no PostgreSQL-specific syntax). Target: SQL Server, MySQL, etc.
--
-- SQL Server: run as-is (CREATE SCHEMA, IDENTITY, CURRENT_TIMESTAMP supported).
-- MySQL: (1) Use "CREATE DATABASE loan_demo; USE loan_demo;" then create schema/tables
--        (2) Replace IDENTITY(1,1) with AUTO_INCREMENT
--        (3) Replace BIT with TINYINT(1); CURRENT_TIMESTAMP is supported.
--        (4) If no schemas, use table names without "loan_analytics." prefix.

-- Schema
CREATE SCHEMA loan_analytics;

-- Dimension: customers
CREATE TABLE loan_analytics.dim_customers (
  customer_id        BIGINT PRIMARY KEY,
  age                INT,
  annual_income_nzd  DECIMAL(12,2),
  employment_type    VARCHAR(100),
  region             VARCHAR(100),
  credit_score       INT,
  tenure_months      INT,
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: products
CREATE TABLE loan_analytics.dim_products (
  product_type       VARCHAR(50) PRIMARY KEY,
  secured_flag       BIT,
  base_risk_tier     VARCHAR(50)
);

-- Dimension: channels
CREATE TABLE loan_analytics.dim_channels (
  channel            VARCHAR(50) PRIMARY KEY,
  channel_group      VARCHAR(50)
);

-- Fact: loans
CREATE TABLE loan_analytics.fct_loans (
  loan_id            BIGINT PRIMARY KEY,
  customer_id        BIGINT NOT NULL,
  product_type       VARCHAR(50) NOT NULL,
  origination_date   DATE NOT NULL,
  principal_nzd      DECIMAL(14,2) NOT NULL,
  interest_rate_apr DECIMAL(6,4) NOT NULL,
  term_months        INT NOT NULL,
  channel            VARCHAR(50) NOT NULL,
  status             VARCHAR(20) DEFAULT 'Active',
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES loan_analytics.dim_customers(customer_id)
);

CREATE INDEX idx_loans_customer ON loan_analytics.fct_loans(customer_id);
CREATE INDEX idx_loans_origdate ON loan_analytics.fct_loans(origination_date);

-- Fact: schedule (use IDENTITY for SQL Server; for MySQL use AUTO_INCREMENT on schedule_id)
CREATE TABLE loan_analytics.fct_schedule (
  schedule_id        BIGINT IDENTITY(1,1) PRIMARY KEY,
  loan_id            BIGINT NOT NULL,
  installment_no     INT NOT NULL,
  due_date           DATE NOT NULL,
  scheduled_amount   DECIMAL(14,2) NOT NULL,
  scheduled_principal DECIMAL(14,2) NOT NULL,
  scheduled_interest  DECIMAL(14,2) NOT NULL,
  FOREIGN KEY (loan_id) REFERENCES loan_analytics.fct_loans(loan_id)
);

CREATE INDEX idx_schedule_loan_due ON loan_analytics.fct_schedule(loan_id, due_date);

-- Fact: payments
CREATE TABLE loan_analytics.fct_payments (
  payment_id         BIGINT IDENTITY(1,1) PRIMARY KEY,
  loan_id            BIGINT NOT NULL,
  payment_date       DATE NOT NULL,
  paid_amount        DECIMAL(14,2) NOT NULL,
  FOREIGN KEY (loan_id) REFERENCES loan_analytics.fct_loans(loan_id)
);

CREATE INDEX idx_payments_loan_date ON loan_analytics.fct_payments(loan_id, payment_date);

-- Fact: collections
CREATE TABLE loan_analytics.fct_collections (
  collection_id      BIGINT IDENTITY(1,1) PRIMARY KEY,
  loan_id            BIGINT NOT NULL,
  event_date         DATE NOT NULL,
  action_type        VARCHAR(50),
  promised_to_pay_date DATE,
  FOREIGN KEY (loan_id) REFERENCES loan_analytics.fct_loans(loan_id)
);

CREATE INDEX idx_collections_loan_date ON loan_analytics.fct_collections(loan_id, event_date);

-- Dimension: macro monthly
CREATE TABLE loan_analytics.dim_macro_monthly (
  month              DATE PRIMARY KEY,
  unemployment_rate  DECIMAL(6,4),
  cpi_index          DECIMAL(10,4),
  cash_rate          DECIMAL(6,4)
);

-- ========== INSERT SAMPLE DATA ==========

-- dim_customers (from dim_customers_sample.csv)
INSERT INTO loan_analytics.dim_customers (customer_id, age, annual_income_nzd, employment_type, region, credit_score, tenure_months) VALUES
(1, 31, 135681, 'Contractor', 'Auckland', 729, 29),
(2, 51, 108295, 'Salaried', 'Wellington', 797, 70),
(3, 62, 122803, 'Self-employed', 'Canterbury', 619, 39),
(4, 37, 140595, 'Self-employed', 'Auckland', 697, 83),
(5, 42, 84378, 'Salaried', 'Auckland', 786, 34),
(6, 29, 107286, 'Contractor', 'Auckland', 613, 108),
(7, 36, 79321, 'Salaried', 'Canterbury', 692, 20),
(8, 49, 109992, 'Self-employed', 'Wellington', 650, 104),
(9, 57, 43966, 'Salaried', 'Auckland', 725, 77),
(10, 49, 78093, 'Contractor', 'Wellington', 722, 84);

-- dim_products (reference data)
INSERT INTO loan_analytics.dim_products (product_type, secured_flag, base_risk_tier) VALUES
('Personal', 0, 'Standard'),
('Auto', 1, 'Standard'),
('Mortgage', 1, 'Low'),
('SME', 0, 'High');

-- dim_channels (reference data)
INSERT INTO loan_analytics.dim_channels (channel, channel_group) VALUES
('Branch', 'Direct'),
('Broker', 'Third Party'),
('Online', 'Direct'),
('Partner', 'Third Party');

-- fct_loans (from fct_loans_sample.csv)
INSERT INTO loan_analytics.fct_loans (loan_id, customer_id, product_type, origination_date, principal_nzd, interest_rate_apr, term_months, channel, status) VALUES
(1001, 1, 'Personal', '2024-01-01', 94459, 0.177, 12, 'Online', 'Active'),
(1002, 2, 'Auto', '2024-02-01', 434535, 0.1359, 60, 'Branch', 'Active'),
(1003, 3, 'Personal', '2024-03-01', 418300, 0.1779, 36, 'Online', 'Active'),
(1004, 4, 'Personal', '2024-04-01', 227321, 0.1576, 24, 'Online', 'Active'),
(1005, 5, 'Auto', '2024-05-01', 310811, 0.1731, 24, 'Broker', 'Active'),
(1006, 6, 'Mortgage', '2024-06-01', 301927, 0.0529, 12, 'Broker', 'Active'),
(1007, 7, 'Personal', '2024-07-01', 52397, 0.0667, 60, 'Branch', 'Active'),
(1008, 8, 'Mortgage', '2024-08-01', 106661, 0.0973, 24, 'Online', 'Active'),
(1009, 9, 'Personal', '2024-09-01', 350034, 0.1047, 60, 'Online', 'Active'),
(1010, 10, 'Mortgage', '2024-10-01', 302081, 0.1528, 24, 'Online', 'Active');

-- fct_payments (from fct_payments_sample.csv)
INSERT INTO loan_analytics.fct_payments (loan_id, payment_date, paid_amount) VALUES
(1001, '2024-02-01', 463),
(1001, '2024-02-16', 739),
(1001, '2024-03-02', 997),
(1002, '2024-03-17', 887),
(1002, '2024-04-01', 1966),
(1002, '2024-04-16', 1116),
(1003, '2024-05-01', 1987),
(1003, '2024-05-16', 1113),
(1003, '2024-05-31', 1873),
(1004, '2024-06-15', 274),
(1004, '2024-06-30', 687),
(1004, '2024-07-15', 499),
(1005, '2024-07-30', 1733),
(1005, '2024-08-14', 571),
(1005, '2024-08-29', 922),
(1006, '2024-09-13', 359),
(1006, '2024-09-28', 300),
(1006, '2024-10-13', 529),
(1007, '2024-10-28', 337),
(1007, '2024-11-12', 541),
(1007, '2024-11-27', 1279),
(1008, '2024-12-12', 1780),
(1008, '2024-12-27', 1454),
(1008, '2025-01-11', 563),
(1009, '2025-01-26', 1057),
(1009, '2025-02-10', 1431),
(1009, '2025-02-25', 947),
(1010, '2025-03-12', 924),
(1010, '2025-03-27', 1586),
(1010, '2025-04-11', 1761);
