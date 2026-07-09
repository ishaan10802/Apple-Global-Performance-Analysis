# app.py
# Main Streamlit application
# Run with: streamlit run app.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
import sys, os

st.set_page_config(
    page_title="Apple Global Performance Analysis",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
import os
sys.path.append(os.path.dirname(__file__))


# ── Cached data loaders ───────────────────────────────────────────
# @st.cache_data ensures database is queried only once per session.
# This prevents reloading on every user interaction.

@st.cache_data(ttl=60)
def load_exec():
    from analytics.db_connector import query
    return query("SELECT * FROM vw_executive_summary ORDER BY fiscal_year,fiscal_quarter")

@st.cache_data(ttl=60)
def load_product():
    from analytics.db_connector import query
    return query("SELECT * FROM vw_product_margin ORDER BY fiscal_year,fiscal_quarter")

@st.cache_data(ttl=60)
def load_regional():
    from analytics.db_connector import query
    return query("SELECT * FROM vw_regional_kpi ORDER BY fiscal_year,fiscal_quarter")

@st.cache_data(ttl=60)
def load_services():
    from analytics.db_connector import query
    return query("SELECT * FROM vw_services_growth ORDER BY fiscal_year,fiscal_quarter")

@st.cache_data(ttl=60)
def load_rfm():
    from analytics.rfm_analysis import run_rfm
    return run_rfm()

@st.cache_data(ttl=60)
def load_cohort():
    from analytics.cohort_analysis import run_cohort
    return run_cohort()

@st.cache_data(ttl=60)
def load_forecasts():
    from analytics.forecasting import run_forecasts
    return run_forecasts(periods=6)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍎 APPLE GLOBAL PERFORMANCE ANALYSIS")
    st.markdown("*Business Analytics Platform*")
    st.markdown("---")
    page = st.radio("Agenda", [
        "📊 Executive Overview",
        "📦 Product Analysis",
        "🌍 Global Performance",
        "📈 Revenue Forecasting",
        "👥 Customer Segmentation",
        "🤖 Analytics Assistant",
    ])
    st.markdown("---")
    st.caption("Data: FY2022–FY2026 Q1")
    st.caption("Source: Apple SEC Filings")
    st.caption("50,000 customer records")

    # Inside the `with st.sidebar:` block, after the navigation radio:
    st.markdown("---")
    if st.button("🔄 Refresh Data", help="Clears cache and reloads from database"):
        st.cache_data.clear()
        st.rerun()


# ── Helper: KPI Card ──────────────────────────────────────────────
def kpi_card(label, value, delta=None, delta_suffix=''):
    if delta is not None:
        color = "#30D158" if delta >= 0 else "#FF453A"
        arrow = "▲" if delta >= 0 else "▼"
        d_text = f'<p style="color:{color};font-size:13px;margin:0">{arrow} {abs(delta):.1f}{delta_suffix}</p>'
    else:
        d_text = ''
    st.markdown(f"""
        <div style="background:#2C2C2E;border-radius:14px;padding:18px 22px;
                    border:1px solid rgba(255,255,255,0.06);">
            <p style="color:#98989D;font-size:11px;text-transform:uppercase;
                      letter-spacing:0.5px;margin:0">{label}</p>
            <p style="color:#F5F5F7;font-size:26px;font-weight:600;
                      margin:6px 0 4px;letter-spacing:-0.5px">{value}</p>
            {d_text}
        </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE OVERVIEW
# ════════════════════════════════════════════════════════════════════
if page == "📊 Executive Overview":

    st.title("Executive Overview")
    st.caption("Top-line performance · FY2022–FY2026 Q1")

    exec_df = load_exec()

    latest = exec_df.iloc[-1]
    prior = exec_df.iloc[-2] if len(exec_df) > 1 else latest

    st.markdown("""
    <div style="
    background:#1C1C1E;
    padding:28px 32px;
    border-radius:16px;
    border-top:3px solid #4F6682;
    margin-top:18px;
    margin-bottom:24px;
    box-shadow:0 4px 24px rgba(0,0,0,0.40);;">

    <div style="
    display:flex;
    align-items:center;
    gap:10px;
    margin-bottom:20px;
    padding-bottom:14px;
    border-bottom:1px solid rgba(255,255,255,0.08);">

    <span style="
    font-size:11px;
    font-weight:600;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:#F5F5F7;">
    Key Findings
    </span>

    <span style="
    font-size:11px;
    color:rgba(255,255,255,0.25);">
    •
    </span>

    <span style="
    font-size:11px;
    letter-spacing:0.06em;
    text-transform:uppercase;
    color:rgba(255,255,255,0.45);">
    BUSINESS HIGHLIGHTS
    </span>

    </div>

   <div style="display:grid;gap:14px;">

   <div style="
   background:rgba(255,255,255,0.055);
   border-radius:10px;
   padding:15px 18px;">

   <div style="
   color:#30D158;
   font-size:11px;
   font-weight:600;
   letter-spacing:0.08em;
   text-transform:uppercase;
   margin-bottom:8px;">
   PROFITABILITY TRANSFORMATION
   </div>

   <div style="
   color:#F5F5F7;
   font-size:14px;
   line-height:1.7;">
   &bull; Services delivered <b>$30.0B</b> revenue at nearly <b>2× Hardware margins</b>.<br>
   &bull; <b>~76% gross margin</b> continues strengthening Apple's earnings quality.
   </div>

   </div>

   <div style="
   background:rgba(255,255,255,0.04);
   border-radius:10px;
   padding:15px 18px;">

   <div style="
   color:#FF9F0A;
   font-size:11px;
   font-weight:600;
   letter-spacing:0.08em;
   text-transform:uppercase;
   margin-bottom:8px;">
   REVENUE CONCENTRATION
   </div>

   <div style="
   color:#F5F5F7;
   font-size:14px;
   line-height:1.7;">
   &bull; iPhone remained the primary driver of <b>FY2026 Q1</b> growth.<br>
   &bull; Revenue concentration remains Apple's key portfolio risk.
   </div>

   </div>

   <div style="
   background:rgba(255,255,255,0.04);
   border-radius:10px;
   padding:15px 18px;">

   <div style="
   color:#64D2FF;
   font-size:11px;
   font-weight:600;
   letter-spacing:0.08em;
   text-transform:uppercase;
   margin-bottom:8px;">
   STRATEGIC GEOGRAPHIC POSITIONING
   </div>

   <div style="
   color:#F5F5F7;
   font-size:14px;
   line-height:1.7;">
   &bull; Americas generated <b>42.6%</b> of Apple's total revenue.<br>
   &bull; India represents Apple's strongest long-term diversification opportunity.
   </div>

   </div>

   </div>

   </div>
   """, unsafe_allow_html=True)

    # ==========================
    # KPI CARDS
    # ==========================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card(
            "Total Revenue",
            f"${latest['total_revenue_millions']/1000:,.1f}B",
            float(latest['qoq_growth_pct']) if latest['qoq_growth_pct'] else None,
            "%"
        )

    with col2:
        kpi_card(
            "Services Revenue",
            f"${latest['services_revenue_millions']/1000:,.1f}B",
            float(latest['services_mix_pct']) if latest['services_mix_pct'] else None,
            "% Mix"
        )

    with col3:
        margin_delta = (
            float(latest['blended_gross_margin_pct'] or 0)
            - float(prior['blended_gross_margin_pct'] or 0)
        )

        kpi_card(
            "Blended Gross Margin",
            f"{latest['blended_gross_margin_pct']:.1f}%",
            round(margin_delta, 1),
            " pp"
        )

    with col4:
        kpi_card(
            "TTM Revenue",
            f"${latest['ttm_revenue_millions']/1000:,.1f}B",
            None
        )
    st.markdown("---")

    # ==========================
    # CHARTS
    # ==========================

    from visualizations.charts import (
        chart_revenue_stack,
        chart_margin_comparison,
        chart_services_growth
    )

    st.plotly_chart(
        chart_revenue_stack(),
        use_container_width=True
    )
    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #0A84FF;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#0A84FF;">Revenue & Margin Signal</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">FY2026 Q1</span>
    </div>

    <div style="display:grid;gap:12px;">

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">Revenue</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;"> 
      &#8226;  FY2026 Q1 revenue grew 40.3%, led by iPhone.<br> 
      &#8226;  Growth remains concentrated within the flagship product portfolio. 
    </p> 
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,159,10,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF9F0A;letter-spacing:0.08em;text-transform:uppercase;">Margin Signal</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &#8226;  Hardware mix reduced blended gross margin.<br>
      &#8226;  Services continues supporting overall profitability.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &#8226;Services expansion offsets hardware margin pressure.<br>
      &#8226;Gross profit growth remains the key board metric.
    </p>
    </div>

    </div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.plotly_chart(
            chart_margin_comparison(),
            use_container_width=True
        )

    with c2:
        st.plotly_chart(
            chart_services_growth(),
            use_container_width=True
        )

    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #30D158;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#30D158;">Services Insights</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">Margin Structure & Mix Dynamics · FY2022–FY2026 Q1</span>
    </div>

    <div style="display:grid;gap:12px;">

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">Margin Premium</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &#8226; Services margins consistently exceed hardware by nearly 2×.<br>
      &#8226; High-margin mix strengthens long-term profitability.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(100,210,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#64D2FF;letter-spacing:0.08em;text-transform:uppercase;">Composition</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &#8226; Services reached a record $30.0B in FY2026 Q1.<br>
      &#8226; Diversified ecosystem reduces hardware cycle dependence.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &#8226; Recurring Services revenue improves earnings resilience.<br>
      &#8226; Expanding mix supports sustainable margin expansion.
    </p>
    </div>

    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================
    # ── Quarterly Revenue Summary ─────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #FF9F0A;margin-top:20px;margin-bottom:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#FF9F0A;">Quarterly Revenue Summary</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">Last 10 Quarters</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    summary_df = (
        exec_df[["quarter_label", "total_revenue_millions", "ttm_revenue_millions"]]
        .tail(10).copy().reset_index(drop=True)
    )
    summary_df.columns = ["Fiscal Quarter", "Revenue ($M)", "TTM Revenue ($M)"]

    st.dataframe(
        summary_df.style
            .format({"Revenue ($M)": "${:,.0f}", "TTM Revenue ($M)": "${:,.0f}"})
            .set_properties(**{
                "background-color": "#2C2C2E",
                "color": "#F5F5F7",
                "border-color": "rgba(255,255,255,0.06)",
                "font-size": "13.5px",
            })
            .set_properties(subset=["Fiscal Quarter"], **{
                "color": "#FF9F0A",
                "font-weight": "500",
            })
            .set_properties(subset=["TTM Revenue ($M)"], **{
                "color": "#30D158",
            })
            .set_table_styles([
                {"selector": "thead th", "props": [
                    ("background-color", "#1C1C1E"),
                    ("color", "rgba(255,255,255,0.4)"),
                    ("font-size", "11px"),
                    ("font-weight", "600"),
                    ("letter-spacing", "0.08em"),
                    ("text-transform", "uppercase"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.1)"),
                    ("padding", "10px 14px"),
                ]},
                {"selector": "tbody tr:hover td", "props": [
                    ("background-color", "rgba(255,159,10,0.06)"),
                ]},
                {"selector": "td", "props": [
                    ("padding", "10px 14px"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.04)"),
                ]},
                {"selector": "", "props": [
                    ("border-radius", "10px"),
                    ("overflow", "hidden"),
                ]},
            ]),
        use_container_width=True,
        hide_index=True,
    )

# ════════════════════════════════════════════════════════════════════
# PAGE 2 — Product Analysis
# ════════════════════════════════════════════════════════════════════
elif page == "📦 Product Analysis":
    st.title("Product Analysis")
    st.caption("Revenue Mix · Gross Margin · Product P&L · FY2022–FY2026 Q1")

    from visualizations.charts import chart_treemap, chart_yoy_heatmap
    from analytics.margin_analysis import run_margin

    margin_data = run_margin()

    # ==========================
    # YoY REVENUE GROWTH HEATMAP
    # ==========================
    st.plotly_chart(
        chart_yoy_heatmap(),
        use_container_width=True
    )

    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #FF9F0A;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#FF9F0A;">Product Insights</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">YoY Growth Pattern & Volatility · FY2023 Q1–FY2026 Q1</span>
    </div>

    <div style="display:grid;gap:12px;">

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">Services Stability</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Services delivered positive YoY growth every quarter.<br>
      &bull; Growth remained the portfolio's most consistent.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,159,10,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF9F0A;letter-spacing:0.08em;text-transform:uppercase;">Hardware Volatility</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Mac and iPad showed the highest volatility.<br>
      &bull; Performance remained heavily launch-cycle driven.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,69,58,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF453A;letter-spacing:0.08em;text-transform:uppercase;">Wearables Drag</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Mac and iPad showed the highest volatility.<br>
      &bull; Performance remained heavily launch-cycle driven.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; FY2026 Q1 delivered broad-based product growth.<br>
      &bull; Portfolio momentum strengthened across all categories.
    </p>
    </div>

    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #30D158;margin-top:28px;margin-bottom:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#30D158;">Product P&L</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">Trailing Twelve Months</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    pl = margin_data['pl_table'].copy()
    pl['ttm_units'] = pl['ttm_units'].apply(
        lambda x: f"{x:.1f}M" if pd.notnull(x) and x > 0 else "—"
    )
    pl_display = pl.rename(columns={
        'product_name': 'Product',
        'ttm_rev_m':    'TTM Revenue',
        'ttm_gp_m':     'Gross Profit',
        'avg_margin':   'Gross Margin',
        'ttm_units':    'Units (TTM)',
        'rev_mix_pct':  'Revenue Mix',
        'gp_mix_pct':   'GP Mix',
    }).reset_index(drop=True)

    def margin_color(val):
        if val >= 70:
            return "color:#30D158;font-weight:500"
        elif val >= 38:
            return "color:#64D2FF;font-weight:500"
        else:
            return "color:#FF9F0A;font-weight:500"

    st.dataframe(
        pl_display.style
            .format({
                'TTM Revenue':  '${:,.0f}M',
                'Gross Profit': '${:,.0f}M',
                'Gross Margin': '{:.1f}%',
                'Revenue Mix':  '{:.1f}%',
                'GP Mix':       '{:.1f}%',
            })
            .map(margin_color, subset=['Gross Margin'])
            .set_properties(**{
                "background-color": "#2C2C2E",
                "color": "#F5F5F7",
                "border-color": "rgba(255,255,255,0.06)",
                "font-size": "13.5px",
            })
            .set_properties(subset=['Product'], **{
                "color": "#F5F5F7",
                "font-weight": "500",
            })
            .bar(subset=['Revenue Mix'], color='rgba(48,209,88,0.25)', vmin=0, vmax=60)
            .set_table_styles([
                {"selector": "thead th", "props": [
                    ("background-color", "#1C1C1E"),
                    ("color", "rgba(255,255,255,0.4)"),
                    ("font-size", "11px"),
                    ("font-weight", "600"),
                    ("letter-spacing", "0.08em"),
                    ("text-transform", "uppercase"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.1)"),
                    ("padding", "10px 14px"),
                ]},
                {"selector": "tbody tr:hover td", "props": [
                    ("background-color", "rgba(48,209,88,0.05)"),
                ]},
                {"selector": "td", "props": [
                    ("padding", "10px 14px"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.04)"),
                ]},
            ]),
        hide_index=True,
        use_container_width=True,
    )

    # ==========================
    # PRODUCT DEEP-DIVE
    # ==========================
    st.markdown("---")
    st.subheader("Product Deep-Dive")

    # Confirmed against live vw_product_margin schema (diagnose_schema.py):
    # fiscal_year, fiscal_quarter, quarter_label, product_name,
    # product_category, gross_margin_tier, revenue_usd_millions,
    # gross_profit_usd_millions, gross_margin_pct, units_millions,
    # revenue_mix_pct, ytd_revenue_millions
    product_df = load_product()
    product_names = sorted(product_df['product_name'].unique().tolist())
    sel_product = st.selectbox(
        "Select product",
        product_names,
        key="product_deep_dive_select"
    )

    df_sel = (
        product_df[product_df['product_name'] == sel_product]
        .sort_values(['fiscal_year', 'fiscal_quarter'])
        .reset_index(drop=True)
    )

    import plotly.graph_objects as go

    fig_deepdive = go.Figure()
    fig_deepdive.add_trace(go.Bar(
        x=df_sel['quarter_label'],
        y=df_sel['revenue_usd_millions'],
        name='Revenue',
        marker_color='#0A84FF',
        yaxis='y1',
    ))
    fig_deepdive.add_trace(go.Scatter(
        x=df_sel['quarter_label'],
        y=df_sel['gross_margin_pct'],
        name='Gross Margin %',
        mode='lines+markers',
        line=dict(color='#30D158', width=2),
        marker=dict(size=6),
        yaxis='y2',
    ))
    fig_deepdive.update_layout(
        title=f"{sel_product} — Revenue & Margin History",
        template='plotly_dark',
        paper_bgcolor='#1C1C1E',
        plot_bgcolor='#1C1C1E',
        font=dict(color='#F5F5F7'),
        yaxis=dict(title='Revenue ($M)'),
        yaxis2=dict(title='Gross Margin %', overlaying='y', side='right', showgrid=False),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(t=60, l=10, r=10, b=10),
        height=420,
    )
    st.plotly_chart(fig_deepdive, use_container_width=True)

    # ── Fully data-driven Product Deep-Dive summary ─────────────────
    # Every number below is computed live from df_sel (this product's
    # quarterly history), product_df (cross-product comparison), and
    # the forecasting model's holdout MAPE — nothing hardcoded per product.
    _COLOR = {
        'green':  ('rgba(48,209,88,0.15)',  '#30D158'),
        'orange': ('rgba(255,159,10,0.15)', '#FF9F0A'),
        'red':    ('rgba(255,69,58,0.15)',  '#FF453A'),
        'blue':   ('rgba(100,210,255,0.12)', '#64D2FF'),
    }
 
    def _pct_change(new, old):
        try:
            if old in (0, None) or pd.isna(old) or pd.isna(new):
                return None
            return (new - old) / old * 100
        except Exception:
            return None
 
    try:
        n_q = len(df_sel)
        latest_row = df_sel.iloc[-1]
        latest_rev = latest_row['revenue_usd_millions']
        latest_margin = latest_row['gross_margin_pct']
        latest_q = latest_row['quarter_label']
 
        # YoY: same fiscal_quarter, one fiscal_year earlier
        yoy_match = df_sel[
            (df_sel['fiscal_quarter'] == latest_row['fiscal_quarter']) &
            (df_sel['fiscal_year'] == latest_row['fiscal_year'] - 1)
        ]
        if not yoy_match.empty:
            yoy_row = yoy_match.iloc[0]
            yoy_rev_pct = _pct_change(latest_rev, yoy_row['revenue_usd_millions'])
            yoy_margin_pp = latest_margin - yoy_row['gross_margin_pct']
            yoy_q = yoy_row['quarter_label']
        else:
            yoy_rev_pct, yoy_margin_pp, yoy_q = None, None, None
 
        rev_max = df_sel['revenue_usd_millions'].max()
        rev_max_q = df_sel.loc[df_sel['revenue_usd_millions'].idxmax(), 'quarter_label']
        is_rev_record = latest_rev >= rev_max - 1e-9
 
        margin_max = df_sel['gross_margin_pct'].max()
        margin_max_q = df_sel.loc[df_sel['gross_margin_pct'].idxmax(), 'quarter_label']
        is_margin_record = latest_margin >= margin_max - 1e-9
 
        # seasonality: average revenue by fiscal quarter, vs overall average
        seasonal = df_sel.groupby('fiscal_quarter')['revenue_usd_millions'].mean()
        overall_avg = df_sel['revenue_usd_millions'].mean()
        peak_fq = int(seasonal.idxmax()) if len(seasonal) > 1 else None
        seasonal_lift_pct = _pct_change(seasonal.max(), overall_avg) if peak_fq is not None else None
 
        # cross-product volatility ranking (std of QoQ % change, all products)
        vol_by_product = (
            product_df.groupby('product_name')['revenue_usd_millions']
            .apply(lambda s: s.pct_change().std())
            .dropna()
            .sort_values(ascending=False)
        )
        if sel_product in vol_by_product.index:
            vol_rank = int(vol_by_product.index.get_loc(sel_product)) + 1
            vol_total = len(vol_by_product)
        else:
            vol_rank, vol_total = None, None
 
        # revenue/margin co-movement (correlation of QoQ diffs)
        rev_diff = df_sel['revenue_usd_millions'].diff()
        margin_diff = df_sel['gross_margin_pct'].diff()
        valid = rev_diff.notna() & margin_diff.notna()
        corr = rev_diff[valid].corr(margin_diff[valid]) if valid.sum() > 2 else None
 
        # this product's live forecast holdout MAPE, if the model has run
        mape = None
        try:
            _fc = load_forecasts()
            if sel_product in _fc['by_product']:
                mape = float(_fc['by_product'][sel_product]['mape'].iloc[0])
        except Exception:
            pass
 
        # ── Block 1: revenue positioning ────────────────────────────
        blocks = []
        if is_rev_record:
            yoy_txt = f" That's {yoy_rev_pct:+.1f}% versus {yoy_q} a year earlier." if yoy_rev_pct is not None else ""
            blocks.append(('green', 'New Revenue High',
                f"{sel_product} revenue reached ${latest_rev/1000:,.1f}B in {latest_q}, the highest "
                f"quarter across the {n_q}-quarter history in this database.{yoy_txt}"
            ))
        else:
            gap_pct = _pct_change(latest_rev, rev_max)
            tone = 'green' if (yoy_rev_pct or 0) >= 0 else 'orange'
            yoy_txt = f", {yoy_rev_pct:+.1f}% versus {yoy_q} a year ago" if yoy_rev_pct is not None else ""
            blocks.append((tone, 'Off Series Peak',
                f"{sel_product} revenue is ${latest_rev/1000:,.1f}B in {latest_q}, "
                f"{abs(gap_pct):.1f}% below the series high of ${rev_max/1000:,.1f}B set in {rev_max_q}{yoy_txt}."
            ))
 
        # ── Block 2: margin positioning ──────────────────────────────
        if is_margin_record:
            yoy_txt = f" ({yoy_margin_pp:+.1f}pp vs. {yoy_q} a year earlier)" if yoy_margin_pp is not None else ""
            blocks.append(('green', 'New Margin High',
                f"Gross margin hit {latest_margin:.1f}% in {latest_q}, the best print across the "
                f"{n_q}-quarter history{yoy_txt}."
            ))
        else:
            gap_pp = latest_margin - margin_max
            tone = 'green' if (yoy_margin_pp or 0) >= 0 else 'orange'
            yoy_txt = f", {yoy_margin_pp:+.1f}pp versus {yoy_q} a year ago" if yoy_margin_pp is not None else ""
            blocks.append((tone, 'Off Margin Peak',
                f"Gross margin is {latest_margin:.1f}% in {latest_q}, {abs(gap_pp):.1f}pp below the "
                f"series high of {margin_max:.1f}% set in {margin_max_q}{yoy_txt}."
            ))
 
        # ── Block 3: pattern — seasonality if strong, else volatility rank ──
        if peak_fq is not None and seasonal_lift_pct is not None and seasonal_lift_pct > 8:
            blocks.append(('blue', 'Seasonal Pattern',
                f"On average, {sel_product} revenue peaks in fiscal Q{peak_fq}, running "
                f"{seasonal_lift_pct:.0f}% above its own quarterly average across all {n_q} quarters — "
                f"a repeatable seasonal shape rather than a one-off spike."
            ))
        elif vol_rank is not None:
            if vol_rank <= 2:
                tone, descriptor = 'red', 'one of the most volatile products'
            elif vol_rank >= vol_total - 1:
                tone, descriptor = 'green', 'one of the steadiest products'
            else:
                tone, descriptor = 'blue', 'mid-pack for volatility among the products'
            blocks.append((tone, 'Volatility Ranking',
                f"{sel_product} ranks #{vol_rank} of {vol_total} products by quarter-to-quarter "
                f"revenue swings — {descriptor} in this dashboard."
            ))
        else:
            blocks.append(('blue', 'Limited History',
                f"Only {n_q} quarters of data are available for {sel_product}, which isn't yet enough "
                f"to establish a reliable seasonal or volatility pattern."
            ))
 
        # ── Inference: ties volatility rank + live forecast MAPE + co-movement ──
        inference_sentences = []
        if vol_rank == 1:
            inference_sentences.append(
                f"{sel_product} is the single most volatile revenue line in the portfolio quarter-to-quarter.")
        elif vol_total is not None and vol_rank == vol_total:
            inference_sentences.append(
                f"{sel_product} is the steadiest revenue line in the portfolio quarter-to-quarter.")
        if mape is not None:
            if mape < 8:
                inference_sentences.append(
                    f"The forecasting model's live holdout error for this segment is {mape:.1f}% MAPE, "
                    f"among the lowest in the portfolio, so near-term guidance here can be tighter than most."
                )
            else:
                inference_sentences.append(
                    f"The forecasting model's live holdout error for this segment is {mape:.1f}% MAPE, "
                    f"among the higher rates in the portfolio, so near-term guidance here should carry wider bands."
                )
        if corr is not None and abs(corr) > 0.3:
            if corr > 0:
                inference_sentences.append(
                    "Revenue and margin have historically moved in the same direction here, so a swing "
                    "in one is likely to show up in the other."
                )
            else:
                inference_sentences.append(
                    "Revenue and margin have historically moved in opposite directions here — growth "
                    "has often come with margin pressure, and vice versa."
                )
        if not inference_sentences:
            inference_sentences.append(
                f"Keep tracking {sel_product}'s revenue and margin together each quarter — there isn't "
                f"yet a strong enough pattern in this data to call a clear trend."
            )
        inference_text = " ".join(inference_sentences)
 
        subtitle = f"{sel_product} · {df_sel['quarter_label'].iloc[0]}–{latest_q} · Live Computed Summary"
 
        _blocks_html = ""
        for _tone, _label, _text in blocks:
            _bg, _fg = _COLOR[_tone]
            _blocks_html += f"""
    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:{_bg};border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:{_fg};letter-spacing:0.08em;text-transform:uppercase;">{_label}</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">{_text}</p>
    </div>
"""
        st.markdown(f"""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #64D2FF;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">
 
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#64D2FF;">Product Intelligence</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">{subtitle}</span>
    </div>
 
    <div style="display:grid;gap:12px;">
{_blocks_html}
    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">{inference_text}</p>
    </div>
 
    </div>
    </div>
    """, unsafe_allow_html=True)
 
    except Exception as _e:
        st.info(f"Product Deep-Dive summary couldn't be computed for {sel_product}: {_e}")
 
# ════════════════════════════════════════════════════════════════════
# PAGE 3 — Global PERFORMANCE
# ════════════════════════════════════════════════════════════════════
elif page == "🌍 Global Performance":
    st.title("Global Performance")
    st.caption("Geographic Revenue · China Risk Monitor · Regional Growth")

    from visualizations.charts import (chart_regional_donut,
                                        chart_china_risk,
                                        chart_regional_growth)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_regional_donut(), use_container_width=True)
    with c2:
        st.plotly_chart(
            chart_china_risk(),
            use_container_width=True
        )

    st.plotly_chart(chart_regional_growth(), use_container_width=True)

    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #64D2FF;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#64D2FF;">Regional Revenue Mix & Risk Monitor</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">FY2022–FY2026 Q1</span>
    </div>

    <div style="display:grid;gap:12px;">

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">Core Markets</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Americas remained Apple's largest revenue contributor.<br>
      &bull; Europe continued delivering stable long-term growth.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,69,58,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF453A;letter-spacing:0.08em;text-transform:uppercase;">China Risk</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; China revenue share continued declining since FY2022.<br>
      &bull; Sustained weakness increases regional concentration risk.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,159,10,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF9F0A;letter-spacing:0.08em;text-transform:uppercase;">Asia Pacific Opportunity</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Asia Pacific offers significant long-term expansion potential.<br>
      &bull; India remains a strategic growth opportunity.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Americas remains Apple's primary earnings engine.<br>
      &bull; China weakness reinforces regional diversification priorities.<br>
      &bull; India offers the strongest long-term expansion opportunity.
    </p>
    </div>

    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #64D2FF;margin-top:28px;margin-bottom:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#64D2FF;">Regional KPI Table</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">Latest Quarter</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    reg_df = load_regional()
    latest_reg = reg_df[reg_df['fiscal_year'] == reg_df['fiscal_year'].max()][[
        'region_name', 'revenue_usd_millions', 'region_share_pct', 'qoq_growth_pct'
    ]].copy().reset_index(drop=True)
    latest_reg.columns = ['Region', 'Revenue ($M)', 'Share %', 'QoQ Growth %']

    def qoq_color(val):
        if val >= 30:
            return "color:#30D158;font-weight:500"
        elif val >= 0:
            return "color:#64D2FF;font-weight:500"
        else:
            return "color:#FF453A;font-weight:500"

    def share_color(val):
        if val >= 40:
            return "color:#F5F5F7;font-weight:500"
        elif val >= 20:
            return "color:#D1D1D6"
        else:
            return "color:#8E8E93"

    st.dataframe(
        latest_reg.style
            .format({
                'Revenue ($M)':  '${:,.0f}',
                'Share %':       '{:.1f}%',
                'QoQ Growth %':  '{:+.1f}%',
            })
            .map(qoq_color,   subset=['QoQ Growth %'])
            .map(share_color, subset=['Share %'])
            .set_properties(**{
                "background-color": "#2C2C2E",
                "color": "#F5F5F7",
                "border-color": "rgba(255,255,255,0.06)",
                "font-size": "13.5px",
            })
            .set_properties(subset=['Region'], **{
                "color": "#F5F5F7",
                "font-weight": "500",
            })
            .bar(subset=['Share %'], color='rgba(100,210,255,0.2)', vmin=0, vmax=50)
            .set_table_styles([
                {"selector": "thead th", "props": [
                    ("background-color", "#1C1C1E"),
                    ("color", "rgba(255,255,255,0.4)"),
                    ("font-size", "11px"),
                    ("font-weight", "600"),
                    ("letter-spacing", "0.08em"),
                    ("text-transform", "uppercase"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.1)"),
                    ("padding", "10px 14px"),
                ]},
                {"selector": "tbody tr:hover td", "props": [
                    ("background-color", "rgba(100,210,255,0.05)"),
                ]},
                {"selector": "td", "props": [
                    ("padding", "10px 14px"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.04)"),
                ]},
            ]),
        hide_index=True,
        use_container_width=True,
    )

# ════════════════════════════════════════════════════════════════════
# PAGE 4 — REVENUE FORECASTING
# ════════════════════════════════════════════════════════════════════
elif page == "📈 Revenue Forecasting":
    st.title("Revenue Forecasting")
    st.caption("6-Quarter Forward Projection ·  Seasonal Revenue Forecasting · Confidence Intervals")
    # Add immediately after every forecast chart's st.plotly_chart() call

    st.caption(
        "Forecasts are generated using historical Apple revenue trends "
        "and observed seasonal patterns. Accuracy is evaluated using "
        "out-of-sample holdout testing (MAPE)."
    )

    with st.spinner("Running forecast models..."):
        forecasts = load_forecasts()

    from visualizations.charts import chart_forecast

    products = list(forecasts['by_product'].keys())
    sel_prod = st.selectbox("Select product to forecast", products,
                             index=products.index('Services') if 'Services' in products else 0)

    if sel_prod in forecasts['by_product']:
        df_f = forecasts['by_product'][sel_prod]
        st.plotly_chart(chart_forecast(sel_prod, df_f),
                         use_container_width=True)

        # Forecast table
        forecast_only = df_f[df_f['type'] == 'Forecast'][[
            'quarter_label', 'revenue_m', 'lo', 'hi'
        ]].copy().reset_index(drop=True)

        forecast_only.index = forecast_only.index + 1
        forecast_only.columns = ['Quarter', 'Forecast ($M)', 'Low Estimate', 'High Estimate']

        # Show MAPE as a caption once, not in every row
        mape_val = df_f['mape'].iloc[0]
        st.caption(
            f"Model:  Seasonal Revenue Forecasting  · "
            f"Holdout MAPE: {mape_val:.1f}% · "
            f"Confidence interval: ±8%"
        )

        st.dataframe(
            forecast_only.style
                .hide(axis='index')
                .format({
                    'Forecast ($M)':  '${:,.0f}',
                    'Low Estimate':   '${:,.0f}',
                    'High Estimate':  '${:,.0f}',
                }),
            hide_index=True,
            use_container_width=True,
        )
    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #FF9F0A;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#FF9F0A;">6-Quarter Forward Projection </span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;"> Holdout MAPE Validation</span>
    </div>

    <div style="display:grid;gap:12px;">

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">High Accuracy</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Services delivered the highest forecast accuracy.<br>
      &bull; Wearables and iPad remained predictably forecastable.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,159,10,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF9F0A;letter-spacing:0.08em;text-transform:uppercase;">Elevated Risk</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; iPhone and Mac carried the highest forecast uncertainty.<br>
      &bull; Product launches continue driving forecast volatility.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">Services Path</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Services revenue is projected to expand steadily.<br>
      &bull; High-margin recurring growth remains structurally resilient.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,69,58,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF453A;letter-spacing:0.08em;text-transform:uppercase;">Wearables Risk</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Wearables continues following a declining trajectory.<br>
      &bull; Product innovation remains the primary recovery catalyst.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Services should anchor long-term financial planning.<br>
      &bull; Broader guidance is warranted for hardware forecasts.
    </p>
    </div>

    </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #BF94FF;margin-top:28px;margin-bottom:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#BF94FF;">All Products Forecast Summary</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">Next Quarter</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    rows = []
    for p, df_p in forecasts['by_product'].items():
        last_actual    = df_p[df_p['type'] == 'Actual']['revenue_m'].iloc[-1]
        first_forecast = df_p[df_p['type'] == 'Forecast']['revenue_m'].iloc[0]
        mape           = df_p['mape'].iloc[0]
        rows.append({
            'Product':              p,
            'Last Actual ($M)':     round(last_actual, 0),
            'Next Q Forecast ($M)': round(first_forecast, 0),
            'Forecast Change %':    round((first_forecast - last_actual) / last_actual * 100, 1),
            'Model MAPE %':         round(mape, 1),
        })
    forecast_df = pd.DataFrame(rows)

    def mape_color(val):
        if val <= 5:
            return "color:#30D158;font-weight:500"
        elif val <= 10:
            return "color:#FF9F0A;font-weight:500"
        else:
            return "color:#FF453A;font-weight:500"

    def change_color(val):
        if val >= 0:
            return "color:#30D158;font-weight:500"
        else:
            return "color:#FF453A;font-weight:500"

    st.dataframe(
        forecast_df.style
            .format({
                'Last Actual ($M)':     '${:,.0f}',
                'Next Q Forecast ($M)': '${:,.0f}',
                'Forecast Change %':    '{:+.1f}%',
                'Model MAPE %':         '{:.1f}%',
            })
            .map(mape_color,   subset=['Model MAPE %'])
            .map(change_color, subset=['Forecast Change %'])
            .set_properties(**{
                "background-color": "#2C2C2E",
                "color": "#F5F5F7",
                "border-color": "rgba(255,255,255,0.06)",
                "font-size": "13.5px",
            })
            .set_properties(subset=['Product'], **{
                "color": "#F5F5F7",
                "font-weight": "500",
            })
            .bar(
                subset=['Forecast Change %'],
                color=['rgba(255,69,58,0.25)', 'rgba(48,209,88,0.25)'],
                align='zero', vmin=-45, vmax=10,
            )
            .set_table_styles([
                {"selector": "thead th", "props": [
                    ("background-color", "#1C1C1E"),
                    ("color", "rgba(255,255,255,0.4)"),
                    ("font-size", "11px"),
                    ("font-weight", "600"),
                    ("letter-spacing", "0.08em"),
                    ("text-transform", "uppercase"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.1)"),
                    ("padding", "10px 14px"),
                ]},
                {"selector": "tbody tr:hover td", "props": [
                    ("background-color", "rgba(191,148,255,0.05)"),
                ]},
                {"selector": "td", "props": [
                    ("padding", "10px 14px"),
                    ("border-bottom", "1px solid rgba(255,255,255,0.04)"),
                ]},
            ]),
        hide_index=True,
        use_container_width=True,
    )

# ════════════════════════════════════════════════════════════════════
# PAGE 5 — Customer Segmentation
# ════════════════════════════════════════════════════════════════════
elif page == "👥 Customer Segmentation":
    st.title("Customer Segmentation")
    st.caption("RFM segmentation · Cohort Retention ")
    st.info("""
About this dataset: Apple does not publicly disclose customer-level purchase data, cohort histories, or retention metrics. This section uses 50,000 synthetic customer records generated to realistically simulate behavioral patterns within Apple's ecosystem (FY2019–FY2025).

The analytical techniques demonstrated here—including RFM segmentation and cohort retention analysis—are widely used across retail, subscription, SaaS, and e-commerce businesses that maintain transaction-level customer histories.

Revenue values in this section are simulated for analytical demonstration purposes. They do not represent Apple's reported financial results and are not intended to reconcile with Apple's SEC-reported revenue.
""")
    with st.spinner("Running Synthetic Customer Intelligence..."):
        rfm_data    = load_rfm()
        cohort_data = load_cohort()

    from visualizations.charts import chart_rfm_segments, chart_cohort_heatmap

    # KPI row
    c1, c2, c3 = st.columns(3)
    smry = rfm_data['summary']
    champ = smry[smry['segment_name'] == 'Champions']
    with c1:
        kpi_card("Total Customers",
                 f"{rfm_data['detail'].shape[0]:,}", None)
    with c2:
        rev_share = champ['rev_share_pct'].values[0] if len(champ) > 0 else 0
        kpi_card("Champions Revenue Share",
                 f"{rev_share:.1f}%", None)
    with c3:
        kpi_card("Avg Q1 Retention",
                 f"{cohort_data['avg_q1_retention']}%", None)

    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(
            chart_rfm_segments(smry),
            use_container_width=True
        )
    with col2:
        # Confirmed via diagnose_schema.py: run_cohort() returns a dict
        # with the retention matrix under the key 'matrix'
        # (25 cohorts × columns ['Q+0', 'Q+1', 'Q+2', 'Q+3', 'Q+4', 'Q+5']).
        st.plotly_chart(
            chart_cohort_heatmap(cohort_data['matrix']),
            use_container_width=True
        )
    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #0A84FF;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#0A84FF;">Revenue Concentration & RFM Risk</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">Synthetic Dataset</span>
    </div>

    <div style="display:grid;gap:12px;">

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">Concentration</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Champions and Loyal Customers generated nearly 89% revenue.<br>
      &bull; Revenue remains concentrated within two customer segments.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,159,10,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF9F0A;letter-spacing:0.08em;text-transform:uppercase;">Early Warning</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; At-Risk customers currently represent a limited share.<br>
      &bull; Monitor trends before revenue concentration deteriorates.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Retaining premium customers protects long-term revenue.<br>
      &bull; Early intervention reduces future churn exposure.
    </p>
    </div>

    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #30D158;margin-top:20px;margin-bottom:15px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#30D158;">Cohort Retention Matrix</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">Q+0 through Q+5</span>
    </div>

    <div style="display:grid;gap:12px;">

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(48,209,88,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#30D158;letter-spacing:0.08em;text-transform:uppercase;">Early Strength</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Early cohorts maintained exceptionally high retention.<br>
      &bull; Apple's ecosystem continues driving customer stickiness.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(255,159,10,0.15);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#FF9F0A;letter-spacing:0.08em;text-transform:uppercase;">Mid-Term Decay</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Retention gradually declined after Q+3.<br>
      &bull; Services attachment helps sustain long-term engagement.
    </p>
    </div>

    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:14px;">
    <div style="background:rgba(191,148,255,0.12);border-radius:6px;padding:5px 10px;min-width:110px;text-align:center;flex-shrink:0;">
    <span style="font-size:11px;font-weight:600;color:#BF94FF;letter-spacing:0.08em;text-transform:uppercase;">Inference</span>
    </div>
    <p style="margin:0;font-size:13.5px;color:#D1D1D6;line-height:1.65;">
      &bull; Q+3 marks the key customer intervention window.<br>
      &bull; Services adoption supports higher lifetime value.
    </p>
    </div>

    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1C1C1E;padding:28px 32px;border-radius:16px;border-top:3px solid #0A84FF;margin-top:28px;margin-bottom:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
    <span style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#0A84FF;">RFM Segment Detail — Synthetic Dataset</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.25);">·</span>
    <span style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:0.06em;text-transform:uppercase;">50,000 Records</span>
    </div>
    </div>
    """, unsafe_allow_html=True)
    rfm_display = (
        smry.rename(columns={
            "segment_name": "Customer Segment",
            "customers": "Customers",
            "avg_revenue": "Avg Revenue / Customer",
            "median_revenue": "Median Revenue",
            "total_rev": "Revenue",
            "avg_orders": "Avg Orders",
            "avg_clv": "Average CLV",
            "subscriber_pct": "Subscriber %",
            "rev_share_pct": "Revenue Mix",
            "clv_share_pct": "CLV Share",
        })
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )

    # Convert Revenue from USD to USD Millions
    rfm_display["Revenue"] = rfm_display["Revenue"] / 1_000_000

    SEGMENT_COLORS = {
        "Champions": "#30D158",
        "Loyal Customers": "#64D2FF",
        "Potential Loyalists": "#FF9F0A",
        "Promising": "#FF9F0A",
        "New Customers": "#BF94FF",
        "Needs Attention": "#FF9F0A",
        "At Risk": "#FF453A",
        "Lost Customers": "#FF453A",
    }

    def segment_color(val):
        color = SEGMENT_COLORS.get(val, "#F5F5F7")
        return f"color:{color};font-weight:600"

    def rev_share_color(val):
        if val >= 40:
            return "color:#30D158;font-weight:600"
        elif val >= 5:
            return "color:#64D2FF;font-weight:600"
        elif val >= 1:
            return "color:#FF9F0A;font-weight:500"
        else:
            return "color:#FF453A;font-weight:500"

    st.dataframe(
        rfm_display.style
            .format({
                "Customers": "{:,.0f}",
                "Avg Revenue / Customer": "${:,.0f}",
                "Median Revenue": "${:,.0f}",
                "Revenue": "${:,.1f}M",
                "Avg Orders": "{:.1f}",
                "Average CLV": "${:,.0f}",
                "Subscriber %": "{:.1f}%",
                "Revenue Mix": "{:.1f}%",
                "CLV Share": "{:.1f}%",
            })
            .map(segment_color, subset=["Customer Segment"])
            .map(rev_share_color, subset=["Revenue Mix"])
            .bar(
                subset=["Revenue Mix"],
                color="rgba(10,132,255,0.20)",
                vmin=0,
                vmax=50,
            )
            .bar(
                subset=["Customers"],
                color="rgba(255,255,255,0.08)",
            )
            .set_properties(**{
                "background-color": "#2C2C2E",
                "color": "#F5F5F7",
                "border-color": "rgba(255,255,255,0.06)",
                "font-size": "13px",
                "padding": "10px 14px",
                "text-align": "right",
            })
            .set_properties(
                subset=["Customer Segment"],
                **{
                    "text-align": "left",
                    "font-weight": "600",
                    "color": "#F5F5F7",
                },
            )
            .set_table_styles([
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", "#1C1C1E"),
                        ("color", "rgba(255,255,255,0.55)"),
                        ("font-size", "11px"),
                        ("font-weight", "600"),
                        ("letter-spacing", "0.08em"),
                        ("text-transform", "uppercase"),
                        ("text-align", "center"),
                        ("padding", "12px 14px"),
                        ("border-bottom", "1px solid rgba(255,255,255,0.10)"),
                    ],
                },
                {
                    "selector": "tbody td",
                    "props": [
                        ("border-bottom", "1px solid rgba(255,255,255,0.04)"),
                        ("vertical-align", "middle"),
                    ],
                },
                {
                    "selector": "tbody tr:hover td",
                    "props": [
                        ("background-color", "rgba(10,132,255,0.06)"),
                    ],
                },
            ]),
        hide_index=True,
        use_container_width=True,
    )


    
# ════════════════════════════════════════════════════════════════════
# PAGE 6 — AI INSIGHTS
# ════════════════════════════════════════════════════════════════════
elif page == "🤖 Analytics Assistant":
    st.title("Customer Analytics Assistant")
    st.caption("Powered by GPT-4o · Live data from PostgreSQL warehouse")

    tab = st.tabs(["💬 Ask a Question"])[0]

    
    with tab:
        st.subheader("Ask Anything About Apple's Business")
        st.info("Type any question in plain English. AI analyzes your live database and answers.")
        examples = [
            "Which product had the highest gross margin this year?",
            "How has China's revenue share changed since FY2022?",
            "What is the Services attach rate trend?",
            "Which region is growing the fastest?",
            "How does FY2026 Q1 compare to FY2025 Q1?",
        ]
        sel_ex = st.selectbox("Or choose an example question:", [""] + examples)
        q = st.text_input("Your question:", value=sel_ex if sel_ex else "")
        if st.button("Ask", type="primary") and q:
            with st.spinner("Analyzing..."):
                try:
                    from genai.insight_engine import answer_question
                    answer = answer_question(q)
                    st.markdown("---")
                    st.markdown(f"**Answer:** {answer}")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {e}")  