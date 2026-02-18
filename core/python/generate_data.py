import os
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

@dataclass
class Config:
    seed: int = 42
    n_customers: int = 8000
    n_loans: int = 12000
    start_date: date = date(2022, 1, 1)
    end_date: date = date(2026, 1, 31)
    out_dir: str = "../data/raw"

    product_mix = {"Personal": 0.55, "Auto": 0.20, "Mortgage": 0.15, "SME": 0.10}
    channel_mix = {"Online": 0.35, "Broker": 0.30, "Branch": 0.20, "Partner": 0.15}

    channel_risk = {"Online": 1.05, "Broker": 1.15, "Branch": 0.90, "Partner": 1.25}
    product_risk = {"Personal": 1.25, "Auto": 1.10, "Mortgage": 0.55, "SME": 1.35}

def daterange_random(start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))

def month_add(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    mdays = [31,29 if (y%4==0 and (y%100!=0 or y%400==0)) else 28,31,30,31,30,31,31,30,31,30,31][m-1]
    day = min(d.day, mdays)
    return date(y, m, day)

def annuity_payment(principal: float, annual_rate: float, term_months: int) -> float:
    r = annual_rate / 12.0
    if r <= 0:
        return principal / term_months
    return principal * (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def make_customers(cfg: Config) -> pd.DataFrame:
    random.seed(cfg.seed); np.random.seed(cfg.seed)
    regions = ["Auckland","Wellington","Canterbury","Waikato","Bay of Plenty","Otago","Manawatu","Other"]
    employment = ["Salaried","Self-employed","Contractor","Student","Unemployed"]

    cust_ids = np.arange(1, cfg.n_customers + 1)
    age = np.clip(np.random.normal(38, 12, cfg.n_customers).round().astype(int), 18, 75)
    income = np.clip(np.random.lognormal(mean=10.9, sigma=0.45, size=cfg.n_customers), 18000, 250000).round(2)
    credit = np.clip(np.random.normal(650, 70, cfg.n_customers).round().astype(int), 450, 850)
    tenure = np.clip(np.random.exponential(36, cfg.n_customers).round().astype(int), 1, 180)

    emp = np.random.choice(employment, size=cfg.n_customers, p=[0.58,0.12,0.10,0.10,0.10])
    reg = np.random.choice(regions, size=cfg.n_customers, p=[0.38,0.14,0.14,0.10,0.08,0.06,0.05,0.05])

    return pd.DataFrame({
        "customer_id": cust_ids,
        "age": age,
        "annual_income_nzd": income,
        "employment_type": emp,
        "region": reg,
        "credit_score": credit,
        "tenure_months": tenure
    })

def make_loans(cfg: Config, customers: pd.DataFrame) -> pd.DataFrame:
    random.seed(cfg.seed+1); np.random.seed(cfg.seed+1)
    loan_ids = np.arange(100000, 100000 + cfg.n_loans)
    customer_ids = np.random.choice(customers["customer_id"], size=cfg.n_loans, replace=True)

    products = list(cfg.product_mix.keys())
    prod_p = np.array(list(cfg.product_mix.values()), dtype=float); prod_p /= prod_p.sum()
    product_type = np.random.choice(products, size=cfg.n_loans, p=prod_p)

    channels = list(cfg.channel_mix.keys())
    ch_p = np.array(list(cfg.channel_mix.values()), dtype=float); ch_p /= ch_p.sum()
    channel = np.random.choice(channels, size=cfg.n_loans, p=ch_p)

    orig_dates = [daterange_random(cfg.start_date, cfg.end_date) for _ in range(cfg.n_loans)]

    term = []
    principal = []
    apr = []
    for p in product_type:
        if p == "Mortgage":
            t = int(np.random.choice([120,180,240,300], p=[0.10,0.25,0.40,0.25]))
            amt = float(np.random.lognormal(mean=12.2, sigma=0.35))
            base_apr = np.random.normal(0.072, 0.01)
        elif p == "Auto":
            t = int(np.random.choice([24,36,48,60], p=[0.20,0.35,0.30,0.15]))
            amt = float(np.random.lognormal(mean=10.8, sigma=0.35))
            base_apr = np.random.normal(0.119, 0.02)
        elif p == "SME":
            t = int(np.random.choice([12,18,24,36], p=[0.15,0.25,0.35,0.25]))
            amt = float(np.random.lognormal(mean=11.0, sigma=0.45))
            base_apr = np.random.normal(0.149, 0.03)
        else:
            t = int(np.random.choice([12,24,36,48], p=[0.25,0.35,0.25,0.15]))
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
    rows = []
    for _, r in loans.iterrows():
        loan_id = int(r["loan_id"])
        orig = pd.to_datetime(r["origination_date"]).date()
        term = int(r["term_months"])
        principal = float(r["principal_nzd"])
        rate = float(r["interest_rate_apr"])
        pmt = annuity_payment(principal, rate, term)

        bal = principal
        for n in range(1, term + 1):
            due = month_add(orig, n)
            interest = bal * (rate / 12.0)
            principal_part = max(0.0, min(pmt - interest, bal))
            bal = max(0.0, bal - principal_part)
            rows.append({
                "loan_id": loan_id,
                "installment_no": n,
                "due_date": due,
                "scheduled_amount": round(pmt, 2),
                "scheduled_principal": round(principal_part, 2),
                "scheduled_interest": round(interest, 2)
            })
            if bal <= 0.01:
                break
    return pd.DataFrame(rows)

def generate_payments(cfg: Config, customers: pd.DataFrame, loans: pd.DataFrame, schedule: pd.DataFrame):
    random.seed(cfg.seed+2); np.random.seed(cfg.seed+2)
    cust_map = customers.set_index("customer_id").to_dict(orient="index")

    loan_risk = {}
    for _, l in loans.iterrows():
        c = cust_map[int(l["customer_id"])]
        credit = c["credit_score"]
        income = float(c["annual_income_nzd"])
        emp = c["employment_type"]

        prod = l["product_type"]
        ch = l["channel"]
        rate = float(l["interest_rate_apr"])

        x = 0.0
        x += (650 - credit) / 90.0
        x += (65000 - income) / 90000.0
        x += (rate - 0.12) / 0.08
        if emp in ["Unemployed", "Student"]:
            x += 0.6
        x *= cfg.product_risk[prod] * cfg.channel_risk[ch]

        p_late = float(np.clip(sigmoid(x) * 0.35, 0.02, 0.55))
        p_miss = float(np.clip(sigmoid(x) * 0.12, 0.005, 0.25))
        loan_risk[int(l["loan_id"])] = (p_late, p_miss)

    payments = []
    collections = []

    for _, s in schedule.iterrows():
        loan_id = int(s["loan_id"])
        due = pd.to_datetime(s["due_date"]).date()
        amt = float(s["scheduled_amount"])
        if due > cfg.end_date:
            continue

        p_late, p_miss = loan_risk[loan_id]
        u = random.random()

        if u < p_miss:
            if random.random() < 0.55:
                collections.append({
                    "loan_id": loan_id,
                    "event_date": due + timedelta(days=random.randint(3, 25)),
                    "action_type": random.choice(["SMS","Call","Email","Agent","Hardship"]),
                    "promised_to_pay_date": due + timedelta(days=random.randint(7, 40))
                })
            continue

        late_days = 0
        if u < p_miss + p_late:
            late_days = int(np.random.choice([3,7,14,21,35,60], p=[0.22,0.22,0.20,0.16,0.12,0.08]))
        pay_date = due + timedelta(days=late_days)

        partial = 1.0
        if late_days >= 14 and random.random() < 0.22:
            partial = float(np.random.uniform(0.4, 0.85))

        paid_amt = round(amt * partial, 2)
        payments.append({"loan_id": loan_id, "payment_date": pay_date, "paid_amount": paid_amt})

        if partial < 0.999 and random.random() < 0.65:
            topup_date = pay_date + timedelta(days=random.randint(5, 25))
            topup_amt = round(amt - paid_amt, 2)
            payments.append({"loan_id": loan_id, "payment_date": topup_date, "paid_amount": topup_amt})

    return pd.DataFrame(payments), pd.DataFrame(collections)

def main():
    cfg = Config()
    os.makedirs(cfg.out_dir, exist_ok=True)

    customers = make_customers(cfg)
    loans = make_loans(cfg, customers)
    schedule = build_schedule(loans)
    payments, collections = generate_payments(cfg, customers, loans, schedule)

    customers.to_csv(os.path.join(cfg.out_dir, "dim_customers.csv"), index=False)
    loans.to_csv(os.path.join(cfg.out_dir, "fct_loans.csv"), index=False)
    schedule.to_csv(os.path.join(cfg.out_dir, "fct_schedule.csv"), index=False)
    payments.to_csv(os.path.join(cfg.out_dir, "fct_payments.csv"), index=False)
    collections.to_csv(os.path.join(cfg.out_dir, "fct_collections.csv"), index=False)

    dim_products = pd.DataFrame([
        {"product_type":"Personal","secured_flag":False,"base_risk_tier":"High"},
        {"product_type":"Auto","secured_flag":True,"base_risk_tier":"Medium"},
        {"product_type":"Mortgage","secured_flag":True,"base_risk_tier":"Low"},
        {"product_type":"SME","secured_flag":False,"base_risk_tier":"High"},
    ])
    dim_channels = pd.DataFrame([
        {"channel":"Online","channel_group":"Direct"},
        {"channel":"Branch","channel_group":"Direct"},
        {"channel":"Broker","channel_group":"Indirect"},
        {"channel":"Partner","channel_group":"Indirect"},
    ])
    dim_products.to_csv(os.path.join(cfg.out_dir, "dim_products.csv"), index=False)
    dim_channels.to_csv(os.path.join(cfg.out_dir, "dim_channels.csv"), index=False)

    print("✅ Data generated:", os.path.abspath(cfg.out_dir))

if __name__ == "__main__":
    main()
