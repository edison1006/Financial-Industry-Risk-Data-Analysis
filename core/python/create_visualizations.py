"""
Data Visualization Script for Financial Risk Analysis

Generates key visualizations from SQL marts:
- Delinquency trends over time
- DPD distribution by product/channel
- Migration matrix heatmap
- Vintage analysis curves
- Risk score distribution
- Commercial profitability metrics
"""

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10


def get_engine():
    """Get database engine from DB_URL environment variable."""
    db_url = os.getenv("DB_URL") or os.getenv("PG_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit(
            "Missing database connection. Set DB_URL environment variable.\n"
            "Examples:\n"
            "  DB_URL='sqlite:///loan_demo.db'\n"
            "  DB_URL='mysql+pymysql://user:password@localhost:3306/loan_demo'\n"
            "  DB_URL='mssql+pyodbc://user:password@localhost:1433/loan_demo?driver=ODBC+Driver+17+for+SQL+Server'\n"
            "  DB_URL='postgresql://user:password@localhost:5432/loan_demo'"
        )
    return create_engine(db_url)


def query_to_df(query: str, engine) -> pd.DataFrame:
    """Execute SQL query and return as pandas DataFrame."""
    return pd.read_sql_query(query, engine)


def create_output_dir():
    """Create output directory for visualizations."""
    output_dir = Path(__file__).resolve().parent.parent.parent / "visualizations"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def plot_delinquency_trends(engine, output_dir):
    """Plot delinquency rates (30+, 60+, 90+) over time."""
    query = """
    SELECT
        month_end,
        COUNT(*) AS total_loans,
        AVG(CASE WHEN dpd_bucket IN ('DPD_30_59', 'DPD_60_89', 'DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_30p,
        AVG(CASE WHEN dpd_bucket IN ('DPD_60_89', 'DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p,
        AVG(CASE WHEN dpd_bucket = 'DPD_90_PLUS' THEN 1 ELSE 0 END) AS rate_90p
    FROM mart_portfolio_snapshot
    GROUP BY month_end
    ORDER BY month_end;
    """
    df = query_to_df(query, engine)
    df["month_end"] = pd.to_datetime(df["month_end"])

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df["month_end"], df["rate_30p"] * 100, label="30+ DPD", marker="o", linewidth=2)
    ax.plot(df["month_end"], df["rate_60p"] * 100, label="60+ DPD", marker="s", linewidth=2)
    ax.plot(df["month_end"], df["rate_90p"] * 100, label="90+ DPD", marker="^", linewidth=2)

    ax.set_xlabel("Month End", fontsize=12)
    ax.set_ylabel("Delinquency Rate (%)", fontsize=12)
    ax.set_title("Portfolio Delinquency Trends Over Time", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_path = output_dir / "delinquency_trends.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close()


def plot_dpd_by_product(engine, output_dir):
    """Plot DPD distribution by product type."""
    query = """
    SELECT
        l.product_type,
        s.dpd_bucket,
        COUNT(*) AS loan_count
    FROM mart_portfolio_snapshot s
    JOIN fct_loans l ON s.loan_id = l.loan_id
    GROUP BY l.product_type, s.dpd_bucket
    ORDER BY l.product_type, s.dpd_bucket;
    """
    df = query_to_df(query, engine)

    pivot_df = df.pivot(index="product_type", columns="dpd_bucket", values="loan_count").fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_df.plot(kind="bar", stacked=True, ax=ax, colormap="RdYlGn_r")

    ax.set_xlabel("Product Type", fontsize=12)
    ax.set_ylabel("Number of Loans", fontsize=12)
    ax.set_title("DPD Distribution by Product Type", fontsize=14, fontweight="bold")
    ax.legend(title="DPD Bucket", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()

    output_path = output_dir / "dpd_by_product.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close()


def plot_migration_matrix(engine, output_dir):
    """Plot DPD migration matrix as heatmap."""
    query = """
    SELECT
        from_bucket,
        to_bucket,
        COUNT(*) AS loan_count
    FROM mart_dpd_migration
    GROUP BY from_bucket, to_bucket
    ORDER BY from_bucket, to_bucket;
    """
    df = query_to_df(query, engine)

    pivot_df = df.pivot(index="from_bucket", columns="to_bucket", values="loan_count").fillna(0)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot_df, annot=True, fmt=".0f", cmap="YlOrRd", ax=ax, cbar_kws={"label": "Loan Count"})

    ax.set_xlabel("To Bucket", fontsize=12)
    ax.set_ylabel("From Bucket", fontsize=12)
    ax.set_title("DPD Migration Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout()

    output_path = output_dir / "migration_matrix.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close()


def plot_vintage_analysis(engine, output_dir):
    """Plot vintage curves showing 60+ DPD rate by months on books."""
    query = """
    SELECT
        vintage_month,
        months_on_books,
        AVG(rate_60plus) AS avg_rate_60plus
    FROM mart_vintage_60plus
    GROUP BY vintage_month, months_on_books
    ORDER BY vintage_month, months_on_books;
    """
    df = query_to_df(query, engine)
    df["vintage_month"] = pd.to_datetime(df["vintage_month"])

    fig, ax = plt.subplots(figsize=(14, 7))

    for vintage in sorted(df["vintage_month"].unique()):
        vintage_data = df[df["vintage_month"] == vintage]
        ax.plot(
            vintage_data["months_on_books"],
            vintage_data["avg_rate_60plus"] * 100,
            marker="o",
            label=vintage.strftime("%Y-%m"),
            linewidth=2,
        )

    ax.set_xlabel("Months on Books (MOB)", fontsize=12)
    ax.set_ylabel("60+ DPD Rate (%)", fontsize=12)
    ax.set_title("Vintage Analysis: 60+ DPD Rate by Months on Books", fontsize=14, fontweight="bold")
    ax.legend(title="Vintage", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = output_dir / "vintage_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close()


def plot_risk_scores(engine, output_dir):
    """Plot risk score distribution from watchlist."""
    query = """
    SELECT risk_score
    FROM risk_watchlist
    WHERE risk_score IS NOT NULL;
    """
    try:
        df = query_to_df(query, engine)
    except Exception as e:
        print(f"  Risk watchlist not available. Skipping risk score visualization. ({e})")
        return

    if len(df) == 0:
        print("  No risk scores found. Skipping risk score visualization.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.hist(df["risk_score"], bins=50, edgecolor="black", alpha=0.7, color="steelblue")
    ax1.set_xlabel("Risk Score", fontsize=12)
    ax1.set_ylabel("Frequency", fontsize=12)
    ax1.set_title("Risk Score Distribution", fontsize=13, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    ax2.boxplot(df["risk_score"], vert=True)
    ax2.set_ylabel("Risk Score", fontsize=12)
    ax2.set_title("Risk Score Box Plot", fontsize=13, fontweight="bold")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = output_dir / "risk_scores.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close()


def plot_commercial_metrics(engine, output_dir):
    """Plot commercial profitability metrics (NII, RAR)."""
    query = """
    SELECT
        month_end,
        SUM(nii_est) AS total_nii,
        SUM(rar_profit_est) AS total_rar_profit,
        AVG(rar_profit_est) AS avg_rar_profit
    FROM comm_rar_monthly
    GROUP BY month_end
    ORDER BY month_end;
    """
    try:
        df = query_to_df(query, engine)
    except Exception as e:
        print(f"  Commercial marts not available. Skipping commercial visualization. ({e})")
        return

    if len(df) == 0:
        print("  No commercial data found. Skipping commercial visualization.")
        return

    df["month_end"] = pd.to_datetime(df["month_end"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    ax1.plot(df["month_end"], df["total_nii"], marker="o", linewidth=2, color="green")
    ax1.set_xlabel("Month End", fontsize=12)
    ax1.set_ylabel("Total Net Interest Income", fontsize=12)
    ax1.set_title("Net Interest Income Trend", fontsize=13, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

    ax2.plot(df["month_end"], df["avg_rar_profit"], marker="s", linewidth=2, color="blue")
    ax2.set_xlabel("Month End", fontsize=12)
    ax2.set_ylabel("Average RAR Profit (proxy)", fontsize=12)
    ax2.set_title("Risk-Adjusted Return (Proxy) Trend", fontsize=13, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()

    output_path = output_dir / "commercial_metrics.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close()


def create_interactive_dashboard(engine, output_dir):
    """Create an interactive Plotly dashboard (optional)."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("  Plotly not installed. Skipping interactive dashboard.")
        return

    query = """
    SELECT
        month_end,
        COUNT(*) AS total_loans,
        AVG(CASE WHEN dpd_bucket IN ('DPD_60_89', 'DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
    FROM mart_portfolio_snapshot
    GROUP BY month_end
    ORDER BY month_end;
    """
    df = query_to_df(query, engine)
    df["month_end"] = pd.to_datetime(df["month_end"])

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Delinquency Rate (60+ DPD)", "Portfolio Size", "DPD Distribution", "Summary"),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"type": "pie"}, {"type": "scatter"}],
        ],
    )

    fig.add_trace(
        go.Scatter(
            x=df["month_end"],
            y=df["rate_60p"] * 100,
            name="60+ DPD Rate",
            mode="lines+markers",
            line=dict(color="red"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df["month_end"],
            y=df["total_loans"],
            name="Total Loans",
            mode="lines+markers",
            line=dict(color="blue"),
        ),
        row=1,
        col=2,
    )

    latest = df.iloc[-1]
    fig.add_trace(
        go.Pie(
            labels=["Current", "60+ DPD"],
            values=[
                latest["total_loans"] * (1 - latest["rate_60p"]),
                latest["total_loans"] * latest["rate_60p"],
            ],
            name="DPD Distribution",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(height=800, title_text="Financial Risk Dashboard", showlegend=True)

    output_path = output_dir / "interactive_dashboard.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")


def main():
    """Main function to generate all visualizations."""
    print("Starting visualization generation...")

    engine = get_engine()
    output_dir = create_output_dir()

    try:
        print("\n1. Delinquency trends...")
        plot_delinquency_trends(engine, output_dir)

        print("\n2. DPD by product...")
        plot_dpd_by_product(engine, output_dir)

        print("\n3. Migration matrix...")
        plot_migration_matrix(engine, output_dir)

        print("\n4. Vintage analysis...")
        plot_vintage_analysis(engine, output_dir)

        print("\n5. Risk score distribution...")
        plot_risk_scores(engine, output_dir)

        print("\n6. Commercial metrics...")
        plot_commercial_metrics(engine, output_dir)

        print("\n7. Interactive dashboard...")
        create_interactive_dashboard(engine, output_dir)

        print(f"\nAll visualizations saved to: {output_dir}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
