"""
Quick Test Data Generator for Financial Risk Analysis

Generates smaller, configurable test datasets for quick testing and development.
Use this for rapid iteration and testing without generating the full 12,000 loan dataset.

Usage:
    python generate_test_data.py --customers 100 --loans 200
    python generate_test_data.py --customers 50 --loans 100 --output-dir ./test_data
    python generate_test_data.py --load-to-db  # Generate and load directly to PostgreSQL
"""

import os
import sys
import argparse
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from sqlalchemy import create_engine
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


@dataclass
class TestConfig:
    seed: int = 42
    n_customers: int = 100
    n_loans: int = 200
    start_date: date = date(2022, 1, 1)
    end_date: date = date(2026, 1, 31)
    out_dir: str = "../data/raw"
    load_to_db: bool = False
    
    # Product mix (can be adjusted for testing)
    product_mix = {"Personal": 0.55, "Auto": 0.20, "Mortgage": 0.15, "SME": 0.10}
    channel_mix = {"Online": 0.35, "Broker": 0.30, "Branch": 0.20, "Partner": 0.15}


def daterange_random(start: date, end: date) -> date:
    """Generate random date between start and end."""
    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))


def month_add(d: date, months: int) -> date:
    """Add months to a date."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    mdays = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    day = min(d.day, mdays)
    return date(y, m, day)


def annuity_payment(principal: float, annual_rate: float, term_months: int) -> float:
    """Calculate monthly annuity payment."""
    r = annual_rate / 12.0
    if r <= 0:
        return principal / term_months
    return principal * (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)


def sigmoid(x: float) -> float:
    """Sigmoid function for risk modeling."""
    return 1.0 / (1.0 + math.exp(-x))


def make_customers(cfg: TestConfig) -> pd.DataFrame:
    """Generate customer dimension data."""
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    
    regions = ["Auckland", "Wellington", "Canterbury", "Waikato", "Bay of Plenty", "Otago", "Manawatu", "Other"]
    employment = ["Salaried", "Self-employed", "Contractor", "Student", "Unemployed"]
    
    cust_ids = np.arange(1, cfg.n_customers + 1)
    age = np.clip(np.random.normal(38, 12, cfg.n_customers).round().astype(int), 18, 75)
    income = np.clip(np.random.lognormal(mean=10.9, sigma=0.45, size=cfg.n_customers), 18000, 250000).round(2)
    credit = np.clip(np.random.normal(650, 70, cfg.n_customers).round().astype(int), 450, 850)
    tenure = np.clip(np.random.exponential(36, cfg.n_customers).round().astype(int), 1, 180)
    
    emp = np.random.choice(employment, size=cfg.n_customers, p=[0.58, 0.12, 0.10, 0.10, 0.10])
    reg = np.random.choice(regions, size=cfg.n_customers, p=[0.38, 0.14, 0.14, 0.10, 0.08, 0.06, 0.05, 0.05])
    
    return pd.DataFrame({
        "customer_id": cust_ids,
        "age": age,
        "annual_income_nzd": income,
        "employment_type": emp,
        "region": reg,
        "credit_score": credit,
        "tenure_months": tenure
    })


def make_loans(cfg: TestConfig, customers: pd.DataFrame) -> pd.DataFrame:
    """Generate loan fact data."""
    random.seed(cfg.seed + 1)
    np.random.seed(cfg.seed + 1)
    
    loan_ids = np.arange(100000, 100000 + cfg.n_loans)
    customer_ids = np.random.choice(customers["customer_id"], size=cfg.n_loans, replace=True)
    
    products = list(cfg.product_mix.keys())
    prod_p = np.array(list(cfg.product_mix.values()), dtype=float)
    prod_p /= prod_p.sum()
    product_type = np.random.choice(products, size=cfg.n_loans, p=prod_p)
    
    channels = list(cfg.channel_mix.keys())
    ch_p = np.array(list(cfg.channel_mix.values()), dtype=float)
    ch_p /= ch_p.sum()
    channel = np.random.choice(channels, size=cfg.n_loans, p=ch_p)
    
    orig_dates = [daterange_random(cfg.start_date, cfg.end_date) for _ in range(cfg.n_loans)]
    
    term = []
    principal = []
    apr = []
    
    for p in product_type:
        if p == "Mortgage":
            t = int(np.random.choice([120, 180, 240, 300], p=[0.10, 0.25, 0.40, 0.25]))
            amt = float(np.random.lognormal(mean=12.2, sigma=0.35))
            base_apr = np.random.normal(0.072, 0.01)
        elif p == "Auto":
            t = int(np.random.choice([24, 36, 48, 60], p=[0.20, 0.35, 0.30, 0.15]))
            amt = float(np.random.lognormal(mean=10.8, sigma=0.35))
            base_apr = np.random.normal(0.119, 0.02)
        elif p == "SME":
            t = int(np.random.choice([12, 18, 24, 36], p=[0.15, 0.25, 0.35, 0.25]))
            amt = float(np.random.lognormal(mean=11.0, sigma=0.45))
            base_apr = np.random.normal(0.149, 0.03)
        else:  # Personal
            t = int(np.random.choice([12, 24, 36, 48], p=[0.25, 0.35, 0.25, 0.15]))
            amt = float(np.random.lognormal(mean=10.4, sigma=0.45))
            base_apr = np.random.normal(0.169, 0.04)
        
        term.append(t)
        principal.append(float(np.clip(amt, 2000, 1200000)))
        apr.append(float(np.clip(base_apr, 0.03, 0.39)))
    
    return pd.DataFrame({
        "loan_id": loan_ids,
        "customer_id": customer_ids,
        "product_type": product_type,
        "origination_date": orig_dates,
        "principal_nzd": np.round(principal, 2),
        "interest_rate_apr": np.round(apr, 4),
        "term_months": term,
        "channel": channel,
        "status": "Active"
    })


def build_schedule(loans: pd.DataFrame) -> pd.DataFrame:
    """Build payment schedule for all loans."""
    rows = []
    for _, loan in loans.iterrows():
        loan_id = loan["loan_id"]
        principal = loan["principal_nzd"]
        apr = loan["interest_rate_apr"]
        term = loan["term_months"]
        orig_date = loan["origination_date"]
        
        monthly_pmt = annuity_payment(principal, apr, term)
        remaining = principal
        
        for inst in range(1, term + 1):
            due_date = month_add(orig_date, inst)
            interest = remaining * (apr / 12.0)
            principal_pmt = monthly_pmt - interest
            remaining -= principal_pmt
            
            rows.append({
                "loan_id": loan_id,
                "installment_no": inst,
                "due_date": due_date,
                "scheduled_amount": round(monthly_pmt, 2),
                "scheduled_principal": round(principal_pmt, 2),
                "scheduled_interest": round(interest, 2)
            })
    
    return pd.DataFrame(rows)


def generate_payments(cfg: TestConfig, customers: pd.DataFrame, loans: pd.DataFrame, schedule: pd.DataFrame) -> tuple:
    """Generate payment and collection events with realistic risk behavior."""
    random.seed(cfg.seed + 2)
    np.random.seed(cfg.seed + 2)
    
    customer_lookup = customers.set_index("customer_id")
    loan_lookup = loans.set_index("loan_id")
    
    payments = []
    collections = []
    
    for _, sched in schedule.iterrows():
        loan_id = sched["loan_id"]
        due_date = sched["due_date"]
        scheduled_amt = sched["scheduled_amount"]
        
        loan = loan_lookup.loc[loan_id]
        customer = customer_lookup.loc[loan["customer_id"]]
        
        # Risk factors
        credit_score = customer["credit_score"]
        income = customer["annual_income_nzd"]
        emp_type = customer["employment_type"]
        product = loan["product_type"]
        channel = loan["channel"]
        apr = loan["interest_rate_apr"]
        
        # Risk multipliers
        emp_risk = {"Salaried": 0.8, "Self-employed": 1.1, "Contractor": 1.2, "Student": 1.5, "Unemployed": 2.0}[emp_type]
        prod_risk = {"Mortgage": 0.55, "Auto": 1.1, "Personal": 1.25, "SME": 1.35}[product]
        ch_risk = {"Branch": 0.9, "Online": 1.05, "Broker": 1.15, "Partner": 1.25}[channel]
        
        # Calculate payment probability
        risk_score = (
            (850 - credit_score) / 400.0 +  # Lower credit = higher risk
            (250000 - income) / 250000.0 +  # Lower income = higher risk
            (apr - 0.05) * 5 +  # Higher rate = higher risk
            (emp_risk - 1.0) +
            (prod_risk - 1.0) +
            (ch_risk - 1.0)
        )
        
        pay_prob = sigmoid(-risk_score + 2.0)  # Adjust offset for realistic default rates
        
        # Generate payment
        if random.random() < pay_prob:
            # On-time or slightly late payment
            days_late = max(0, int(np.random.exponential(5)))
            payment_date = due_date + timedelta(days=days_late)
            
            # Sometimes partial payment
            if random.random() < 0.15:  # 15% partial payments
                paid_amt = scheduled_amt * random.uniform(0.3, 0.9)
            else:
                paid_amt = scheduled_amt
            
            payments.append({
                "loan_id": loan_id,
                "payment_date": payment_date,
                "paid_amount": round(paid_amt, 2)
            })
            
            # Generate collection events for late payments
            if days_late > 30:
                collections.append({
                    "loan_id": loan_id,
                    "event_date": payment_date,
                    "action_type": random.choice(["SMS", "Call", "Email", "Agent"]),
                    "promised_to_pay_date": payment_date + timedelta(days=random.randint(7, 30))
                })
    
    return pd.DataFrame(payments), pd.DataFrame(collections)


def load_to_database(df: pd.DataFrame, table_name: str):
    """Load DataFrame directly to database (SQLite-friendly)."""
    db_url = os.getenv("DB_URL") or os.getenv("PG_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit(
            "Missing database connection. Set DB_URL environment variable.\n"
            "Examples: DB_URL='sqlite:///loan_demo.db' or DB_URL='mysql+pymysql://user:password@localhost:3306/loan_demo'"
        )
    
    engine = create_engine(db_url)
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"  Loaded {len(df)} rows to {table_name}")


def main():
    parser = argparse.ArgumentParser(description="Generate test data for Financial Risk Analysis")
    parser.add_argument("--customers", type=int, default=100, help="Number of customers (default: 100)")
    parser.add_argument("--loans", type=int, default=200, help="Number of loans (default: 200)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default="../data/raw", help="Output directory for CSV files")
    parser.add_argument("--load-to-db", action="store_true", help="Load data directly to database")
    
    args = parser.parse_args()
    
    cfg = TestConfig(
        seed=args.seed,
        n_customers=args.customers,
        n_loans=args.loans,
        out_dir=args.output_dir,
        load_to_db=args.load_to_db
    )
    
    print(f"📊 Generating test data...")
    print(f"   Customers: {cfg.n_customers}")
    print(f"   Loans: {cfg.n_loans}")
    print(f"   Seed: {cfg.seed}")
    print(f"   Date range: {cfg.start_date} to {cfg.end_date}")
    
    # Generate data
    customers = make_customers(cfg)
    loans = make_loans(cfg, customers)
    schedule = build_schedule(loans)
    payments, collections = generate_payments(cfg, customers, loans, schedule)
    
    # Dimension tables
    dim_products = pd.DataFrame([
        {"product_type": "Personal", "secured_flag": False, "base_risk_tier": "High"},
        {"product_type": "Auto", "secured_flag": True, "base_risk_tier": "Medium"},
        {"product_type": "Mortgage", "secured_flag": True, "base_risk_tier": "Low"},
        {"product_type": "SME", "secured_flag": False, "base_risk_tier": "High"},
    ])
    dim_channels = pd.DataFrame([
        {"channel": "Online", "channel_group": "Direct"},
        {"channel": "Branch", "channel_group": "Direct"},
        {"channel": "Broker", "channel_group": "Indirect"},
        {"channel": "Partner", "channel_group": "Indirect"},
    ])
    
    if cfg.load_to_db:
        if not DB_AVAILABLE:
            print("❌ Error: sqlalchemy required for database loading")
            print("   Install: pip install sqlalchemy")
            sys.exit(1)
        
        print("\n📥 Loading to database...")
        load_to_database(customers, "dim_customers")
        load_to_database(dim_products, "dim_products")
        load_to_database(dim_channels, "dim_channels")
        load_to_database(loans, "fct_loans")
        load_to_database(schedule, "fct_schedule")
        load_to_database(payments, "fct_payments")
        load_to_database(collections, "fct_collections")
        print("\nData loaded to database successfully!")
    else:
        # Save to CSV
        os.makedirs(cfg.out_dir, exist_ok=True)
        
        customers.to_csv(os.path.join(cfg.out_dir, "dim_customers.csv"), index=False)
        loans.to_csv(os.path.join(cfg.out_dir, "fct_loans.csv"), index=False)
        schedule.to_csv(os.path.join(cfg.out_dir, "fct_schedule.csv"), index=False)
        payments.to_csv(os.path.join(cfg.out_dir, "fct_payments.csv"), index=False)
        collections.to_csv(os.path.join(cfg.out_dir, "fct_collections.csv"), index=False)
        dim_products.to_csv(os.path.join(cfg.out_dir, "dim_products.csv"), index=False)
        dim_channels.to_csv(os.path.join(cfg.out_dir, "dim_channels.csv"), index=False)
        
        print(f"\nData generated: {os.path.abspath(cfg.out_dir)}")
        print(f"\n📊 Summary:")
        print(f"   Customers: {len(customers)}")
        print(f"   Loans: {len(loans)}")
        print(f"   Schedule rows: {len(schedule)}")
        print(f"   Payments: {len(payments)}")
        print(f"   Collections: {len(collections)}")


if __name__ == "__main__":
    main()
