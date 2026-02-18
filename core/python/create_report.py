"""
HTML report generator for Financial Industry Risk Data Analysis.

Creates a single HTML file with key charts embedded (base64) plus a few
high-level portfolio summary tables pulled from the marts.

Typical usage (from repo root):
  python core/python/create_report.py
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import os
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine, text


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = ROOT_DIR / "reports" / "financial_risk_report.html"


def get_engine():
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


def choose_snapshot_view(engine) -> tuple[str, bool]:
    """
    Prefer mart_portfolio_snapshot_v2 when available; fall back to v1.
    Returns (view_name, has_eop_balance).
    """
    try:
        pd.read_sql_query("SELECT 1 FROM mart_portfolio_snapshot_v2 LIMIT 1;", engine)
        return "mart_portfolio_snapshot_v2", True
    except Exception:
        return "mart_portfolio_snapshot", False


def embed_png_as_data_uri(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def df_to_html_table(df: pd.DataFrame, *, index: bool = False) -> str:
    # Keep the HTML small/clean and readable.
    return df.to_html(index=index, border=0, classes="table", justify="left", escape=True)


def safe_read_sql(query: str, engine, params: dict | None = None) -> pd.DataFrame | None:
    try:
        return pd.read_sql_query(text(query), engine, params=params or {})
    except Exception:
        return None


def build_summary_tables(engine) -> dict[str, str]:
    snapshot_view, has_eop = choose_snapshot_view(engine)

    latest_df = safe_read_sql(f"SELECT MAX(month_end) AS latest_month_end FROM {snapshot_view};", engine)
    latest = None
    if latest_df is not None and not latest_df.empty:
        latest = latest_df.iloc[0]["latest_month_end"]

    tables: dict[str, str] = {}

    overview_q = f"""
    SELECT
      COUNT(DISTINCT loan_id) AS loans,
      COUNT(DISTINCT customer_id) AS customers,
      MIN(month_end) AS first_month_end,
      MAX(month_end) AS last_month_end
    FROM {snapshot_view};
    """
    overview_df = safe_read_sql(overview_q, engine)
    if overview_df is not None:
        tables["Portfolio overview"] = df_to_html_table(overview_df)

    if latest is not None:
        latest_metrics_q = f"""
        SELECT
          month_end,
          COUNT(*) AS total_rows,
          COUNT(DISTINCT loan_id) AS loans,
          AVG(CASE WHEN dpd_bucket IN ('DPD_30_59','DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_30p,
          AVG(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p,
          AVG(CASE WHEN dpd_bucket = 'DPD_90_PLUS' THEN 1 ELSE 0 END) AS rate_90p
          {", SUM(eop_balance) AS total_eop_balance" if has_eop else ""}
        FROM {snapshot_view}
        WHERE month_end = :latest
        GROUP BY month_end;
        """
        latest_metrics_df = safe_read_sql(latest_metrics_q, engine, params={"latest": latest})
        if latest_metrics_df is not None:
            for c in ["rate_30p", "rate_60p", "rate_90p"]:
                if c in latest_metrics_df.columns:
                    latest_metrics_df[c] = (latest_metrics_df[c] * 100).round(2)
            tables["Latest month KPIs"] = df_to_html_table(latest_metrics_df)

        product_q = f"""
        SELECT
          product_type,
          COUNT(DISTINCT loan_id) AS loans,
          AVG(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
        FROM {snapshot_view}
        WHERE month_end = :latest
        GROUP BY product_type
        ORDER BY rate_60p DESC, loans DESC
        LIMIT 10;
        """
        product_df = safe_read_sql(product_q, engine, params={"latest": latest})
        if product_df is not None:
            product_df["rate_60p"] = (product_df["rate_60p"] * 100).round(2)
            tables["Top products by 60+ rate (latest month)"] = df_to_html_table(product_df)

        channel_q = f"""
        SELECT
          channel,
          COUNT(DISTINCT loan_id) AS loans,
          AVG(CASE WHEN dpd_bucket IN ('DPD_60_89','DPD_90_PLUS') THEN 1 ELSE 0 END) AS rate_60p
        FROM {snapshot_view}
        WHERE month_end = :latest
        GROUP BY channel
        ORDER BY rate_60p DESC, loans DESC
        LIMIT 10;
        """
        channel_df = safe_read_sql(channel_q, engine, params={"latest": latest})
        if channel_df is not None:
            channel_df["rate_60p"] = (channel_df["rate_60p"] * 100).round(2)
            tables["Top channels by 60+ rate (latest month)"] = df_to_html_table(channel_df)

    return tables


def build_report_html(
    *,
    generated_at: str,
    embedded_images: list[tuple[str, str]],
    extra_links: list[tuple[str, str]],
    tables: dict[str, str],
) -> str:
    def section(title: str, body: str) -> str:
        return f"<section><h2>{html.escape(title)}</h2>{body}</section>"

    css = """
    :root { --fg:#111827; --muted:#6b7280; --bg:#ffffff; --card:#f9fafb; --border:#e5e7eb; }
    body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
           color:var(--fg); background:var(--bg); }
    header { padding:28px 22px; border-bottom:1px solid var(--border); background:linear-gradient(180deg, #ffffff, #f9fafb); }
    header h1 { margin:0 0 6px 0; font-size:22px; }
    header .meta { color:var(--muted); font-size:13px; }
    main { max-width:1100px; margin:0 auto; padding:18px 22px 48px; }
    section { margin-top:18px; padding:16px; background:var(--card); border:1px solid var(--border); border-radius:10px; }
    h2 { margin:0 0 12px 0; font-size:16px; }
    .grid { display:grid; grid-template-columns: 1fr; gap:14px; }
    figure { margin:0; padding:12px; background:#fff; border:1px solid var(--border); border-radius:10px; }
    figure img { max-width:100%; height:auto; display:block; border-radius:8px; }
    figcaption { margin-top:10px; color:var(--muted); font-size:13px; }
    .links a { display:inline-block; margin-right:12px; color:#2563eb; text-decoration:none; }
    .links a:hover { text-decoration:underline; }
    .table { width:100%; border-collapse:collapse; font-size:13px; background:#fff; border:1px solid var(--border); border-radius:10px; overflow:hidden; }
    .table th, .table td { padding:8px 10px; border-bottom:1px solid var(--border); text-align:left; }
    .table th { background:#f3f4f6; font-weight:600; }
    .table tr:last-child td { border-bottom:none; }
    """

    links_html = ""
    if extra_links:
        links_html = '<div class="links">' + "".join(
            f'<a href="{html.escape(href)}">{html.escape(label)}</a>' for label, href in extra_links
        ) + "</div>"

    images_html = ""
    if embedded_images:
        figures = []
        for title, data_uri in embedded_images:
            figures.append(
                "<figure>"
                f'<img alt="{html.escape(title)}" src="{data_uri}"/>'
                f"<figcaption>{html.escape(title)}</figcaption>"
                "</figure>"
            )
        images_html = section("Charts", f'<div class="grid">{"".join(figures)}</div>')

    tables_html = ""
    if tables:
        parts: list[str] = []
        for title, table_html in tables.items():
            parts.append(f"<h3>{html.escape(title)}</h3>{table_html}")
        tables_html = section("Key tables", "".join(parts))

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Financial Risk Report</title>
  <style>{css}</style>
</head>
<body>
  <header>
    <h1>Financial Industry Risk Report</h1>
    <div class="meta">Generated at: {html.escape(generated_at)}</div>
    {links_html}
  </header>
  <main>
    {tables_html}
    {images_html}
  </main>
</body>
</html>
"""
    return html_doc


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a single HTML report (with embedded images).")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output HTML path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--skip-visualizations",
        action="store_true",
        help="Skip regenerating charts; just assemble the report from existing files.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Optionally regenerate charts first.
    if not args.skip_visualizations:
        try:
            import create_visualizations

            create_visualizations.main()
        except Exception as e:
            raise SystemExit(f"Failed to generate visualizations: {e}")

    engine = get_engine()
    try:
        vis_dir = ROOT_DIR / "visualizations"
        expected = [
            ("Portfolio delinquency trends", vis_dir / "delinquency_trends.png"),
            ("DPD distribution by product", vis_dir / "dpd_by_product.png"),
            ("DPD migration matrix", vis_dir / "migration_matrix.png"),
            ("Vintage analysis (60+ DPD by months on books)", vis_dir / "vintage_analysis.png"),
            ("Risk scores distribution (if available)", vis_dir / "risk_scores.png"),
            ("Commercial metrics (if available)", vis_dir / "commercial_metrics.png"),
        ]

        embedded_images: list[tuple[str, str]] = []
        for title, path in expected:
            if path.exists():
                embedded_images.append((title, embed_png_as_data_uri(path)))

        extra_links: list[tuple[str, str]] = []
        interactive = vis_dir / "interactive_dashboard.html"
        if interactive.exists():
            # Make it easy to open the interactive dashboard when present.
            # Use a relative link when report is in ROOT_DIR/reports.
            try:
                rel = os.path.relpath(interactive, output_path.parent)
                extra_links.append(("Interactive dashboard (Plotly)", rel))
            except Exception:
                extra_links.append(("Interactive dashboard (Plotly)", str(interactive)))

        tables = build_summary_tables(engine)
        generated_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")

        report_html = build_report_html(
            generated_at=generated_at,
            embedded_images=embedded_images,
            extra_links=extra_links,
            tables=tables,
        )

        output_path.write_text(report_html, encoding="utf-8")
        print(f"Saved report: {output_path}")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())

