# visualizations/dashboard.py
"""
Standalone HTML Dashboard Exporter.
Builds a single self-contained HTML file that works without
any server — just open in Chrome/Edge.

This is the file you include in your GitHub README as a demo link
and send to recruiters.

Run from project root:
    python visualizations/dashboard.py
"""
import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from visualizations.charts import (
    chart_revenue_stack,
    chart_services_growth,
    chart_margin_comparison,
    chart_treemap,
    chart_yoy_heatmap,
    chart_regional_donut,
    chart_china_risk,
    chart_regional_growth,
)
from analytics.db_connector import query
from analytics.margin_analysis import run_margin


# ── Brand constants ───────────────────────────────────────────────
BG       = "#1C1C1E"
CARD     = "#2C2C2E"
TEXT     = "#F5F5F7"
MUTED    = "#98989D"
BLUE     = "#0071E3"
GREEN    = "#30D158"
BORDER   = "rgba(255,255,255,0.06)"


def get_latest_kpis() -> dict:
    """Pull headline KPIs from warehouse for the KPI card row."""
    df = query("""
        SELECT * FROM vw_executive_summary
        ORDER BY fiscal_year DESC, fiscal_quarter DESC
        LIMIT 2
    """)
    svc = query("""
        SELECT services_attach_rate_pct, services_qoq_growth_pct
        FROM vw_services_growth
        ORDER BY fiscal_year DESC, fiscal_quarter DESC
        LIMIT 1
    """)
    cur   = df.iloc[0].to_dict() if len(df) > 0 else {}
    prior = df.iloc[1].to_dict() if len(df) > 1 else {}
    return {
        "quarter":       cur.get("quarter_label", "Latest Quarter"),
        "total_rev":     round(cur.get("total_revenue_millions", 0) / 1000, 1),
        "services_rev":  round(cur.get("services_revenue_millions", 0) / 1000, 1),
        "margin":        round(cur.get("blended_gross_margin_pct", 0), 1),
        "svc_mix":       round(cur.get("services_mix_pct", 0), 1),
        "qoq_growth":    round(cur.get("qoq_growth_pct", 0) or 0, 1),
        "ttm":           round(cur.get("ttm_revenue_millions", 0) / 1000, 1),
        "attach":        round(
            svc["services_attach_rate_pct"].iloc[0], 1
        ) if len(svc) > 0 else 0,
        "prior_margin":  round(prior.get("blended_gross_margin_pct", 0), 1),
    }


def kpi_cards_html(kpis: dict) -> str:
    """Generate the four top KPI cards as HTML."""
    margin_delta = kpis["margin"] - kpis["prior_margin"]
    margin_color = GREEN if margin_delta >= 0 else "#FF453A"
    margin_arrow = "▲" if margin_delta >= 0 else "▼"
    qoq_color    = GREEN if kpis["qoq_growth"] >= 0 else "#FF453A"
    qoq_arrow    = "▲" if kpis["qoq_growth"] >= 0 else "▼"

    return f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Total Revenue</div>
            <div class="kpi-value">${kpis['total_rev']}B</div>
            <div class="kpi-delta" style="color:{qoq_color}">
                {qoq_arrow} {abs(kpis['qoq_growth']):.1f}% QoQ
            </div>
            <div class="kpi-sub">TTM: ${kpis['ttm']}B</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Services Revenue</div>
            <div class="kpi-value">${kpis['services_rev']}B</div>
            <div class="kpi-delta" style="color:{GREEN}">
                ▲ {kpis['svc_mix']:.1f}% of total revenue
            </div>
            <div class="kpi-sub">Attach rate: {kpis['attach']}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Blended Gross Margin</div>
            <div class="kpi-value">{kpis['margin']}%</div>
            <div class="kpi-delta" style="color:{margin_color}">
                {margin_arrow} {abs(margin_delta):.1f}pp vs prior quarter
            </div>
            <div class="kpi-sub">Services margin ~75.4%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Quarter</div>
            <div class="kpi-value" style="font-size:20px">
                {kpis['quarter']}
            </div>
            <div class="kpi-delta" style="color:{MUTED}">
                Latest complete quarter
            </div>
            <div class="kpi-sub">FY2022–FY2026 Q1 covered</div>
        </div>
    </div>
    """


def chart_to_div(fig, div_id: str) -> str:
    """Convert a Plotly figure to an embeddable HTML div string."""
    fig_json = fig.to_json()
    # Escape single quotes to prevent JS parse errors
    fig_json  = fig_json.replace("'", "\\'")
    return f"""
        <div class="chart-card" id="card_{div_id}">
            <div id="{div_id}"></div>
        </div>
        <script>
            (function(){{
                var d = JSON.parse('{fig_json}');
                Plotly.newPlot('{div_id}', d.data, d.layout,
                               {{responsive:true, displayModeBar:false}});
            }})();
        </script>
    """


def product_pl_table_html() -> str:
    """Generate an HTML table of the product P&L."""
    try:
        margin_data = run_margin()
        pl = margin_data["pl_table"]
        rows = ""
        for _, row in pl.iterrows():
            margin_color = GREEN if row["avg_margin"] > 50 else TEXT
            rows += f"""
            <tr>
                <td>{row['product_name']}</td>
                <td>${row['ttm_rev_m']:,.0f}M</td>
                <td>${row['ttm_gp_m']:,.0f}M</td>
                <td style="color:{margin_color}">{row['avg_margin']:.1f}%</td>
                <td>{row['rev_mix_pct']:.1f}%</td>
                <td>{row['gp_mix_pct']:.1f}%</td>
            </tr>"""
        return f"""
        <div class="chart-card" style="overflow-x:auto">
            <h3 class="section-title">Product P&L — Trailing Twelve Months</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>TTM Revenue</th>
                        <th>TTM Gross Profit</th>
                        <th>Avg Margin</th>
                        <th>Rev Mix</th>
                        <th>GP Mix</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
    except Exception as e:
        return f'<div class="chart-card"><p style="color:{MUTED}">Table unavailable: {e}</p></div>'


def build_html(kpis: dict) -> str:
    """Assemble the complete dashboard HTML string."""

    print("  → Generating charts (this takes ~30 seconds)...")
    charts = {
        "revenue_stack":    chart_revenue_stack(),
        "services_growth":  chart_services_growth(),
        "margin_compare":   chart_margin_comparison(),
        "treemap":          chart_treemap(),
        "yoy_heatmap":      chart_yoy_heatmap(),
        "regional_donut":   chart_regional_donut(),
        "china_risk":       chart_china_risk(),
        "regional_growth":  chart_regional_growth(),
    }
    print("  → Charts generated")

    timestamp  = datetime.now().strftime("%B %d, %Y")
    kpi_html   = kpi_cards_html(kpis)
    pl_html    = product_pl_table_html()

    # Build chart sections
    c_revenue  = chart_to_div(charts["revenue_stack"],   "revenue_stack")
    c_svc      = chart_to_div(charts["services_growth"], "svc_growth")
    c_margin   = chart_to_div(charts["margin_compare"],  "margin_compare")
    c_treemap  = chart_to_div(charts["treemap"],         "treemap")
    c_heatmap  = chart_to_div(charts["yoy_heatmap"],     "yoy_heatmap")
    c_donut    = chart_to_div(charts["regional_donut"],  "reg_donut")
    c_china    = chart_to_div(charts["china_risk"],      "china_risk")
    c_reg_bar  = chart_to_div(charts["regional_growth"], "reg_growth")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Apple Global Performance Analysis Platform</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
*, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
    background:{BG};
    font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display",
                "Helvetica Neue",sans-serif;
    color:{TEXT};
    padding:0 24px 40px;
    min-height:100vh;
}}
.header {{
    padding:32px 0 28px;
    border-bottom:1px solid {BORDER};
    margin-bottom:32px;
    display:flex;
    justify-content:space-between;
    align-items:flex-end;
}}
.header-left h1 {{
    font-size:26px;
    font-weight:700;
    letter-spacing:-0.5px;
    color:{TEXT};
}}
.header-left p {{
    color:{MUTED};
    font-size:13px;
    margin-top:4px;
}}
.header-right {{
    text-align:right;
    color:{MUTED};
    font-size:12px;
}}
.kpi-row {{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:16px;
    margin-bottom:32px;
}}
.kpi-card {{
    background:{CARD};
    border-radius:14px;
    padding:20px 22px;
    border:1px solid {BORDER};
}}
.kpi-label {{
    font-size:11px;
    color:{MUTED};
    text-transform:uppercase;
    letter-spacing:0.6px;
    margin-bottom:8px;
}}
.kpi-value {{
    font-size:28px;
    font-weight:600;
    letter-spacing:-1px;
    margin-bottom:6px;
}}
.kpi-delta {{
    font-size:12px;
    margin-bottom:4px;
}}
.kpi-sub {{
    font-size:11px;
    color:{MUTED};
}}
.section {{
    margin-bottom:28px;
}}
.section-title {{
    font-size:16px;
    font-weight:600;
    color:{TEXT};
    margin-bottom:16px;
    letter-spacing:-0.2px;
    padding:20px 22px 0;
}}
.chart-card {{
    background:{CARD};
    border-radius:14px;
    border:1px solid {BORDER};
    margin-bottom:20px;
    overflow:hidden;
}}
.chart-grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:20px;
    margin-bottom:20px;
}}
.chart-card-full {{
    background:{CARD};
    border-radius:14px;
    border:1px solid {BORDER};
    margin-bottom:20px;
    overflow:hidden;
}}
.data-table {{
    width:100%;
    border-collapse:collapse;
    font-size:13px;
}}
.data-table th {{
    color:{MUTED};
    font-weight:600;
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:0.5px;
    padding:10px 22px;
    text-align:left;
    border-bottom:1px solid {BORDER};
}}
.data-table td {{
    padding:10px 22px;
    color:{TEXT};
    border-bottom:1px solid {BORDER};
}}
.data-table tr:last-child td {{
    border-bottom:none;
}}
.data-table tr:hover td {{
    background:rgba(255,255,255,0.03);
}}
.nav {{
    display:flex;
    gap:8px;
    margin-bottom:28px;
    flex-wrap:wrap;
}}
.nav-btn {{
    background:{CARD};
    border:1px solid {BORDER};
    color:{MUTED};
    padding:8px 18px;
    border-radius:20px;
    cursor:pointer;
    font-size:13px;
    font-family:inherit;
    transition:all 0.2s;
}}
.nav-btn:hover, .nav-btn.active {{
    background:{BLUE};
    color:{TEXT};
    border-color:{BLUE};
}}
.page {{ display:none; }}
.page.active {{ display:block; }}
.footer {{
    color:{MUTED};
    font-size:11px;
    text-align:center;
    padding:32px 0 8px;
    border-top:1px solid {BORDER};
    margin-top:20px;
}}
@media (max-width:768px) {{
    .kpi-row {{ grid-template-columns:1fr 1fr; }}
    .chart-grid {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <h1>🍎 Apple Global Performance Analysis Platform</h1>
        <p>Enterprise analytics · Built on Apple SEC financial disclosures
           · 50,000 customer records · FY2022–FY2026 Q1</p>
    </div>
    <div class="header-right">
        <div>Generated: {timestamp}</div>
        <div style="margin-top:4px">PostgreSQL · Python · Plotly · GPT-4o</div>
    </div>
</div>

{kpi_html}

<nav class="nav">
    <button class="nav-btn active"
            onclick="showPage('overview',this)">
        📊 Executive Overview
    </button>
    <button class="nav-btn"
            onclick="showPage('product',this)">
        📦 Product Analysis
    </button>
    <button class="nav-btn"
            onclick="showPage('regional',this)">
        🌍 Global Performance
    </button>
</nav>

<!-- PAGE 1: EXECUTIVE OVERVIEW -->
<div id="overview" class="page active">
    <div class="section">
        {c_revenue}
    </div>
    <div class="chart-grid">
        {c_svc}
        {c_margin}
    </div>
</div>

<!-- PAGE 2: Product Analysis -->
<div id="product" class="page">
    <div class="section">
        {pl_html}
    </div>
    <div class="section">
        {c_treemap}
    </div>
    <div class="section">
        {c_heatmap}
    </div>
</div>

<!-- PAGE 3: Global Performance -->
<div id="regional" class="page">
    <div class="chart-grid">
        {c_donut}
        {c_china}
    </div>
    <div class="section">
        {c_reg_bar}
    </div>
</div>

<div class="footer">
    Apple Global Performance Analysis &nbsp;·&nbsp;
    Built with PostgreSQL, Python &amp; Plotly &nbsp;·&nbsp;
    Data: Apple public SEC filings (8-K / 10-K / 10-Q) &nbsp;·&nbsp;
    {timestamp}
</div>

<script>
function showPage(id, btn) {{
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
    // Trigger Plotly resize after showing hidden charts
    setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
}}
</script>
</body>
</html>"""


def export_dashboard():
    """Main function — build and save the dashboard HTML."""
    print("\nBuilding Apple Global Performance Analysis Dashboard...")
    print("─" * 50)

    # Pull KPIs
    print("  → Fetching live KPIs from PostgreSQL...")
    kpis = get_latest_kpis()
    print(f"  → Latest quarter: {kpis['quarter']} | "
          f"Revenue: ${kpis['total_rev']}B")

    # Build HTML
    html = build_html(kpis)

    # Save
    out_dir  = os.path.join(
        os.path.dirname(__file__), '..', 'exports', 'reports'
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "apple_dashboard.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(out_path) // 1024
    print(f"\n✅ Dashboard saved: {out_path}")
    print(f"   File size: {size_kb} KB")
    print(f"   Open in browser: file:///{os.path.abspath(out_path)}")
    return out_path


if __name__ == "__main__":
    export_dashboard()