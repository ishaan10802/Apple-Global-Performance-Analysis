# visualizations/charts.py
"""
All Plotly chart functions for the Apple Global Performance Analysis Platform.
Used by both app.py (Streamlit) and dashboard.py (HTML export).

KEY DESIGN RULE:
  base_layout() contains NO 'legend' key.
  Any chart needing a custom legend calls fig.update_layout(legend=...)
  as a SEPARATE second call AFTER applying base_layout().
  This permanently prevents the "multiple values for keyword argument 'legend'" error.
"""

import streamlit as st

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics.db_connector import query

# ── Apple brand color palette ─────────────────────────────────────
C = {
    'blue':   '#0071E3',
    'green':  '#30D158',
    'orange': '#FF9F0A',
    'red':    '#FF453A',
    'purple': '#BF5AF2',
    'gray':   '#6E6E73',
    'bg':     '#1C1C1E',
    'card':   '#2C2C2E',
    'text':   '#F5F5F7',
    'muted':  '#98989D',
}

PRODUCT_COLORS = {
    'iPhone':           C['blue'],
    'Services':         C['green'],
    'Mac':              C['orange'],
    'iPad':             C['purple'],
    'Wearables & Home': C['red'],
    'Accessories':      C['gray'],
}

REGION_COLORS = [
    C['blue'], C['green'], C['orange'], C['purple'], C['red']
]


# ── Base layout ────────────────────────────────────────────────────
# IMPORTANT: This function deliberately contains NO 'legend' key.
# If a chart needs a custom legend, call fig.update_layout(legend=...)
# as a completely separate second call after applying this layout.
def base_layout(title: str = '') -> dict:
    """
    Returns a base Plotly layout dict with Apple dark theme.
    Deliberately excludes 'legend' to avoid keyword conflicts.
    """
    return {
        'title': {
            'text': title,
            'font': {'size': 15, 'color': C['text']},
            'x': 0.02,
        },
        'paper_bgcolor': C['bg'],
        'plot_bgcolor':  C['card'],
        'font': {
            'family': '-apple-system, BlinkMacSystemFont, sans-serif',
            'color':  C['text'],
            'size':   12,
        },
        'xaxis': {
            'showgrid':  False,
            'zeroline':  False,
            'tickfont':  {'color': C['muted']},
        },
        'yaxis': {
            'showgrid':   True,
            'gridcolor':  'rgba(255,255,255,0.06)',
            'zeroline':   False,
            'tickfont':   {'color': C['muted']},
        },
        'margin':    {'l': 60, 'r': 40, 't': 60, 'b': 60},
        'hovermode': 'x unified',
    }
    # NOTE: 'legend' is intentionally absent from this dict.


# ─────────────────────────────────────────────────────────────────
# CHART 1 — Stacked Revenue by Product
# ─────────────────────────────────────────────────────────────────
def chart_revenue_stack() -> go.Figure:
    """
    Stacked bar chart: quarterly revenue by product.
    FY2022 Q1 through FY2026 Q1.
    """
    df = query("""
        SELECT
            quarter_label,
            fiscal_year,
            fiscal_quarter,
            product_name,
            SUM(revenue_usd_millions) AS rev_m
        FROM vw_product_margin
        WHERE fiscal_year >= 2022
        GROUP BY quarter_label, fiscal_year, fiscal_quarter, product_name
        ORDER BY fiscal_year, fiscal_quarter
    """)

    fig = px.bar(
        df,
        x='quarter_label',
        y='rev_m',
        color='product_name',
        color_discrete_map=PRODUCT_COLORS,
        barmode='stack',
        labels={'rev_m': 'Revenue ($M)', 'quarter_label': ''},
    )

    # Step 1: Apply base layout (no legend key inside)
    layout = base_layout('Quarterly Revenue by Product (FY2022–FY2026 Q1)')
    layout['xaxis']['tickangle'] = -35
    fig.update_layout(**layout)

    # Step 2: Apply legend separately — no conflict possible
    fig.update_layout(legend=dict(
        orientation='h',
        y=-0.22,
        x=0,
        bgcolor='rgba(0,0,0,0)',
        font={'color': C['muted'], 'size': 11},
        title_text='',
    ))

    return fig


# ─────────────────────────────────────────────────────────────────
# CHART 2 — Services Growth (Dual-Axis)
# ─────────────────────────────────────────────────────────────────
def chart_services_growth() -> go.Figure:
    """
    Bar + line dual-axis: Services revenue ($M) and attach rate (%).
    """
    df = query("""
        SELECT *
        FROM vw_services_growth
        ORDER BY fiscal_year, fiscal_quarter
    """)

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(
        go.Bar(
            x=df['quarter_label'],
            y=df['services_rev_m'],
            name='Services Revenue ($M)',
            marker_color=C['green'],
            opacity=0.85,
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df['quarter_label'],
            y=df['services_attach_rate_pct'],
            name='Services Mix %',
            line=dict(color=C['orange'], width=2.5),
            mode='lines+markers',
            marker=dict(size=6),
        ),
        secondary_y=True,
    )

    layout = base_layout('Services Revenue & Services Mix Trend')
    layout['xaxis']['tickangle'] = -35
    fig.update_layout(**layout)

    # Legend separately
    fig.update_layout(legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font={'color': C['muted']},
    ))

    fig.update_yaxes(
        title_text='Revenue ($M)',
        secondary_y=False,
        gridcolor='rgba(255,255,255,0.06)',
        tickfont={'color': C['muted']},
    )
    fig.update_yaxes(
        title_text='Services Mix %',
        secondary_y=True,
        ticksuffix='%',
        tickfont={'color': C['muted']},
    )

    return fig


# ─────────────────────────────────────────────────────────────────
# CHART 3 — Gross Margin: Services vs Hardware
# ─────────────────────────────────────────────────────────────────
def chart_margin_comparison() -> go.Figure:
    """
    Line chart: gross margin % over time, split by product category.
    Shows the 36+ percentage point Services premium over Hardware.
    """
    df = query("""
        SELECT
            quarter_label,
            fiscal_year,
            fiscal_quarter,
            product_category,
            ROUND(
                SUM(gross_profit_usd_millions) /
                NULLIF(SUM(revenue_usd_millions), 0) * 100,
                2
            ) AS margin_pct
        FROM vw_product_margin
        GROUP BY quarter_label, fiscal_year, fiscal_quarter, product_category
        ORDER BY fiscal_year, fiscal_quarter
    """)

    fig = px.line(
        df,
        x='quarter_label',
        y='margin_pct',
        color='product_category',
        color_discrete_map={
            'Services': C['green'],
            'Hardware': C['blue'],
        },
        markers=True,
        labels={'margin_pct': 'Gross Margin %', 'quarter_label': ''},
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7))

    layout = base_layout('Gross Margin: Services vs Hardware')
    layout['xaxis']['tickangle'] = -35
    layout['yaxis']['ticksuffix'] = '%'
    layout['yaxis']['range'] = [28, 82]
    fig.update_layout(**layout)

    # Legend separately
    fig.update_layout(legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font={'color': C['muted']},
        title_text='Category',
    ))

    return fig


# ─────────────────────────────────────────────────────────────────
# CHART 4 — Revenue Treemap (Product × Region)
# ─────────────────────────────────────────────────────────────────
def chart_treemap() -> go.Figure:
    """
    Revenue treemap using the latest COMPLETE fiscal year (FY2025).
    FY2026 is excluded because only Q1 is available — partial year
    comparisons are misleading for product mix analysis.
    """
    df = query("""
        SELECT
            p.product_name,
            r.region_name,
            ROUND(SUM(f.revenue_usd_millions), 0) AS rev_m
        FROM fact_revenue  f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_region  r ON f.region_key  = r.region_key
        JOIN dim_date    d ON f.date_key     = d.date_key
        WHERE d.fiscal_year = (
            -- Latest COMPLETE fiscal year (4 quarters)
            SELECT fiscal_year
            FROM (
                SELECT fiscal_year, COUNT(*) AS qtrs
                FROM dim_date
                GROUP BY fiscal_year
                HAVING COUNT(*) = 4
            ) complete_years
            ORDER BY fiscal_year DESC
            LIMIT 1
        )
        GROUP BY p.product_name, r.region_name
    """)

    st.error("USING NEW TREEMAP FUNCTION")
    fig = px.treemap(
        df,
        path=['product_name', 'region_name'],
        values='rev_m',
        color='product_name',
        color_discrete_map=PRODUCT_COLORS,
    )
    fig.update_traces(
        # Clean integer formatting — no more "36,665.67"
        texttemplate='<b>%{label}</b><br>$%{value:,.0f}M<br>%{percentRoot:.0%}',
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}M<extra></extra>',
    )
    fig.update_layout(
        paper_bgcolor=C['bg'],
        font={'family': '-apple-system, sans-serif', 'color': C['text']},
        title={
            'text': 'Revenue Distribution — FY2025 (Latest Complete Year)',
            'font': {'size': 15, 'color': C['text']},
            'x': 0.02,
        },
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# ─────────────────────────────────────────────────────────────────
# CHART 5 — YoY Growth Heatmap
# ─────────────────────────────────────────────────────────────────
def chart_yoy_heatmap() -> go.Figure:

    df = query("""
               
       
        WITH product_quarterly AS (
            SELECT
                d.fiscal_year,
                d.fiscal_quarter,
                d.quarter_label,
                p.product_name,
                SUM(f.revenue_usd_millions) AS total_rev
            FROM fact_revenue    f
            JOIN dim_date        d ON f.date_key    = d.date_key
            JOIN dim_product     p ON f.product_key = p.product_key
            GROUP BY
                d.fiscal_year,
                d.fiscal_quarter,
                d.quarter_label,
                p.product_name
        ),
        with_yoy AS (
            SELECT
                fiscal_year,
                fiscal_quarter,
                quarter_label,
                product_name,
                total_rev,
                LAG(total_rev, 4) OVER (
                    PARTITION BY product_name
                    ORDER BY fiscal_year, fiscal_quarter
                ) AS prior_year_rev
            FROM product_quarterly
        )
        SELECT
            quarter_label,
            product_name,
            ROUND(
                (total_rev - prior_year_rev)
                / NULLIF(prior_year_rev, 0) * 100,
                1
            ) AS yoy_pct
        FROM with_yoy
        WHERE prior_year_rev IS NOT NULL
          AND fiscal_year >= 2023
        ORDER BY fiscal_year, fiscal_quarter, product_name
    """)

    if df.empty:
        return go.Figure()

    pivot = df.pivot(
        index='product_name',
        columns='quarter_label',
        values='yoy_pct',
    )

    # Strategic product ordering — iPhone first (most important)
    order = ['iPhone', 'Services', 'Mac', 'iPad', 'Wearables & Home']
    pivot = pivot.reindex([p for p in order if p in pivot.index])

    # Safe text rendering — empty string for NaN cells
    text_array = []
    for row in pivot.values:
        text_row = []
        for val in row:
            if val is None or (isinstance(val, float) and np.isnan(val)):
                text_row.append('')
            else:
                text_row.append(f'{val:+.1f}%')
        text_array.append(text_row)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.00, '#CC0000'],   # deep red   — large decline
            [0.25, '#FF453A'],   # red        — decline
            [0.40, '#FF9F0A'],   # orange     — slight decline
            [0.50, '#2C2C2E'],   # dark gray  — flat (zero)
            [0.62, '#34C759'],   # light green
            [0.80, '#30D158'],   # green      — growth
            [1.00, '#00A832'],   # deep green — strong growth
        ],
        zmid=0,
        zmin=-35,
        zmax=35,
        text=text_array,
        texttemplate='%{text}',
        textfont=dict(size=11, color='white', family='-apple-system, sans-serif'),
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Quarter: %{x}<br>'
            'YoY Growth: %{z:+.1f}%<extra></extra>'
        ),
        showscale=True,
        colorbar=dict(
            title=dict(text='YoY %', font=dict(color=C['muted'], size=11)),
            tickfont=dict(color=C['muted'], size=10),
            ticksuffix='%',
            thickness=14,
            len=0.9,
        ),
    ))

    layout = base_layout('YoY Revenue Growth — Same Quarter vs Prior Year')
    layout['xaxis']['tickangle'] = -35
    layout['xaxis']['tickfont'] = {'size': 10, 'color': C['muted']}
    layout['yaxis']['tickfont'] = {'size': 11, 'color': C['text']}
    layout['margin'] = {'l': 150, 'r': 80, 't': 60, 'b': 100}
    fig.update_layout(**layout)

    # Source annotation
    fig.add_annotation(
        text=(
            'YoY = (current quarter revenue − same quarter prior year) '
            '÷ prior year × 100. '
            'Computed on aggregate product totals. '
            'Source: Apple SEC 8-K filings FY2022–FY2026.'
        ),
        xref='paper', yref='paper',
        x=0, y=-0.22,
        showarrow=False,
        font=dict(size=9, color=C['muted']),
        xanchor='left',
    )

    return fig

# ─────────────────────────────────────────────────────────────────
# CHART 6 — Regional Revenue Share (Donut)
# ─────────────────────────────────────────────────────────────────
def chart_regional_donut() -> go.Figure:
    """
    Donut chart: revenue share by region for latest fiscal year.
    """
    df = query("""
        SELECT
            region_name,
            ROUND(AVG(region_share_pct), 2) AS share
        FROM vw_regional_kpi
        WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM dim_date)
        GROUP BY region_name
        ORDER BY share DESC
    """)

    fig = go.Figure(go.Pie(
        labels=df['region_name'],
        values=df['share'],
        hole=0.56,
        marker=dict(
            colors=REGION_COLORS,
            line=dict(color=C['bg'], width=2),
        ),
        textinfo='label+percent',
        textfont=dict(size=11, color=C['text']),
        hovertemplate='<b>%{label}</b><br>Share: %{percent}<extra></extra>',
    ))

    fig.update_layout(
        paper_bgcolor=C['bg'],
        font={'family': '-apple-system, sans-serif', 'color': C['text']},
        title={
            'text': 'Revenue by Region — Latest FY',
            'font': {'size': 15, 'color': C['text']},
            'x': 0.02,
        },
        showlegend=False,
        annotations=[{
            'text': 'Region<br>Mix',
            'x': 0.5, 'y': 0.5,
            'font': {'size': 12, 'color': C['muted']},
            'showarrow': False,
        }],
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


# ─────────────────────────────────────────────────────────────────
# CHART 7 — China Risk Monitor (Dual-Axis)
# ─────────────────────────────────────────────────────────────────
def chart_china_risk() -> go.Figure:
    """
    Bar + dotted line: China revenue and share trend.
    Key story: share declined from 19% (FY2022) to ~15% (FY2025).
    """
    df = query("""
        SELECT
            quarter_label,
            fiscal_year,
            fiscal_quarter,
            revenue_usd_millions AS rev_m,
            region_share_pct     AS share_pct,
            qoq_growth_pct       AS qoq_pct
        FROM vw_regional_kpi
        WHERE region_name = 'China'
        ORDER BY fiscal_year, fiscal_quarter
    """)

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(
        go.Bar(
            x=df['quarter_label'],
            y=df['rev_m'],
            name='China Revenue ($M)',
            marker_color=C['orange'],
            opacity=0.8,
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df['quarter_label'],
            y=df['share_pct'],
            name='China Share %',
            line=dict(color=C['red'], width=2.5, dash='dot'),
            mode='lines+markers',
            marker=dict(size=6),
        ),
        secondary_y=True,
    )


    
    layout = base_layout('China Revenue — Geopolitical Risk Monitor')
    layout['xaxis']['tickangle'] = -45
    layout['xaxis']['tickmode']  = 'auto'
    layout['xaxis']['nticks']    = 8   # show every other quarter
    layout['xaxis']['tickfont']  = {'size': 9, 'color': C['muted']}
    fig.update_layout(**layout)

    

    # Legend separately
    fig.update_layout(legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font={'color': C['muted']},
    ))

    fig.update_yaxes(
        title_text='Revenue ($M)',
        secondary_y=False,
        gridcolor='rgba(255,255,255,0.06)',
        tickfont={'color': C['muted']},
    )
    fig.update_yaxes(
        title_text='Region Share %',
        secondary_y=True,
        ticksuffix='%',
        tickfont={'color': C['muted']},
    )

    return fig


# ─────────────────────────────────────────────────────────────────
# CHART 8 — Regional QoQ Growth (Grouped Bar)
# ─────────────────────────────────────────────────────────────────
def chart_regional_growth() -> go.Figure:
    df = query("""
        SELECT quarter_label, fiscal_year, fiscal_quarter,
               region_name, qoq_growth_pct
        FROM vw_regional_kpi
        WHERE qoq_growth_pct IS NOT NULL
          AND fiscal_year >= 2024
        ORDER BY fiscal_year, fiscal_quarter
    """)

    # Apple brand color map — explicit, not sequence
    # Replace the color mapping
    REGION_COLOR_MAP = {
    'Americas':             '#0071E3',   # Apple blue — dominant market
    'Europe':               '#30D158',   # Apple green — second largest
    'China':                '#FF9F0A',   # Apple orange — risk market
    'Japan':                '#BF5AF2',   # Apple purple
    'Rest of Asia Pacific': '#FF453A',   # Apple red
    }
# This matches the same colors used in the regional donut chart
# creating visual consistency across the platform

    fig = px.bar(
        df,
        x='quarter_label',
        y='qoq_growth_pct',
        color='region_name',
        barmode='group',
        color_discrete_map=REGION_COLOR_MAP,   # ← map not sequence
        labels={'qoq_growth_pct': 'QoQ Growth %', 'quarter_label': ''},
    )
    fig.add_hline(
        y=0,
        line_color='rgba(255,255,255,0.25)',
        line_width=1,
    )

    layout = base_layout('Regional Revenue Growth (QoQ %)')
    layout['xaxis']['tickangle'] = -35
    layout['yaxis']['ticksuffix'] = '%'
    fig.update_layout(**layout)

    # Legend separately
    fig.update_layout(legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font={'color': C['muted']},
        title_text='Region',
    ))

    return fig
    
# ─────────────────────────────────────────────────────────────────
# CHART 9 — Revenue Forecast with Confidence Band
# ─────────────────────────────────────────────────────────────────
def chart_forecast(product_name: str, df_product: pd.DataFrame) -> go.Figure:
    """
    Revenue forecast chart with correct chronological x-axis ordering.
    
    ROOT CAUSE OF PREVIOUS BUG:
    Plotly categorical x-axis order = order of FIRST TRACE added.
    Old code added confidence band first → forecast dates became leftmost.
    Fix: add Actual trace first → historical dates become leftmost.
    Then explicitly enforce order via categoryarray.
    """
    actual   = df_product[df_product['type'] == 'Actual'].copy()
    forecast = df_product[df_product['type'] == 'Forecast'].copy()
    color    = PRODUCT_COLORS.get(product_name, C['blue'])
    mape     = df_product['mape'].iloc[0]

    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)

    # Build the EXPLICIT chronological x-axis order.
    # Historical first (FY2022 Q1 → FY2026 Q1),
    # then forecast (FY2026 Q2 → FY2027 Q3).
    # This list is passed to categoryarray to guarantee correct ordering.
    ordered_x = (
        list(actual['quarter_label']) +
        list(forecast['quarter_label'])
    )

    fig = go.Figure()

    # ── TRACE 1: Actual (added first — establishes initial category order) ──
    fig.add_trace(go.Scatter(
        x=actual['quarter_label'],
        y=actual['revenue_m'],
        name='Actual',
        line=dict(color=color, width=2.5),
        mode='lines+markers',
        marker=dict(size=5),
        hovertemplate='%{x}<br>Actual: $%{y:,.0f}M<extra></extra>',
    ))

    # ── TRACE 2: Confidence band (added second — forecast dates appended) ──
    if forecast['hi'].notna().any():
        band_x = (
            list(forecast['quarter_label']) +
            list(forecast['quarter_label'])[::-1]
        )
        band_y = (
            list(forecast['hi'].fillna(0)) +
            list(forecast['lo'].fillna(0))[::-1]
        )
        fig.add_trace(go.Scatter(
            x=band_x,
            y=band_y,
            fill='toself',
            fillcolor=f'rgba({r},{g},{b},0.12)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Confidence band',
            showlegend=True,
            hoverinfo='skip',
        ))

    # ── TRACE 3: Forecast line ──────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=forecast['quarter_label'],
        y=forecast['revenue_m'],
        name='Forecast',
        line=dict(color=color, width=2.5, dash='dash'),
        mode='lines+markers',
        marker=dict(size=6, symbol='diamond'),
        hovertemplate='%{x}<br>Forecast: $%{y:,.0f}M<extra></extra>',
    ))

    # ── Vertical separator at forecast boundary ─────────────────────────────
    if len(actual) > 0:
        fig.add_vline(
            x=actual['quarter_label'].iloc[-1],
            line_color='rgba(255,255,255,0.25)',
            line_dash='dot',
            line_width=1.5,
        )
        # Annotation clarifying the boundary
        fig.add_annotation(
            x=actual['quarter_label'].iloc[-1],
            y=1.0, yref='paper',
            text='← Actual  |  Forecast →',
            showarrow=False,
            font=dict(size=10, color=C['muted']),
            xanchor='center', yanchor='bottom',
        )

    # ── Layout ──────────────────────────────────────────────────────────────
    layout = base_layout(
        f'{product_name} Revenue Forecast  —  Holdout MAPE: {mape:.1f}%'
    )
    layout['xaxis']['tickangle']      = -35
    # CRITICAL: enforce explicit chronological ordering
    layout['xaxis']['categoryorder']  = 'array'
    layout['xaxis']['categoryarray']  = ordered_x
    layout['yaxis']['title']          = 'Revenue ($M)'
    fig.update_layout(**layout)

    fig.update_layout(legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font={'color': C['muted']},
    ))

    return fig

# ─────────────────────────────────────────────────────────────────
# CHART 10 — RFM Segment Revenue Bar
# ─────────────────────────────────────────────────────────────────
def chart_rfm_segments(rfm_summary_df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar: total revenue by RFM customer segment.
    Color-coded by revenue share %.
    """
    df = rfm_summary_df.sort_values('rev_share_pct').copy()

    fig = px.bar(
        df,
        x='rev_share_pct',
        y='segment_name',
        orientation='h',
        color='rev_share_pct',
        color_continuous_scale=['#3A3A3C', C['green']],
        labels={
            
            'segment_name':      'Customer Segment',
            'rev_share_pct':'Revenue Share (%)',
        },
        text='rev_share_pct',
    )
    fig.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside',
    )

    # Build layout without xaxis/yaxis from base (we override them)
    layout = base_layout('Revenue Share by RFM Segment')
    layout.pop('xaxis', None)
    layout.pop('yaxis', None)
    fig.update_layout(**layout)

    # Now set axes and colorscale separately
    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            tickfont={'color': C['muted']},
        ),
        yaxis=dict(
            showgrid=False,
            tickfont={'color': C['muted']},
        ),
        coloraxis_showscale=False,
    )

    return fig


# ─────────────────────────────────────────────────────────────────
# CHART 11 — Cohort Retention Heatmap
# ─────────────────────────────────────────────────────────────────
def chart_cohort_heatmap(matrix_df: pd.DataFrame) -> go.Figure:
    """
    Heatmap: customer retention by cohort × periods since acquisition.
    Shows what % of each cohort is still active after Q+1, Q+2, etc.
    """
    # Limit to last 8 cohorts, first 6 periods for readability
    display = matrix_df.tail(8).iloc[:, :6].copy()

    # Handle NaN values gracefully
    text_vals = np.where(
        np.isnan(display.values.astype(float)),
        '',
        display.values.round(1).astype(str),
    )

    fig = go.Figure(go.Heatmap(
        z=display.values,
        x=display.columns.tolist(),
        y=display.index.tolist(),
        colorscale=[
            [0.0, '#1C1C1E'],
            [0.3, '#FF453A'],
            [0.6, '#FF9F0A'],
            [1.0, '#30D158'],
        ],
        zmin=0,
        zmax=100,
        text=text_vals,
        texttemplate='%{text}%',
        textfont=dict(size=11, color='white'),
        hovertemplate=(
            'Cohort %{y}<br>%{x}: %{z:.1f}% retained<extra></extra>'
        ),
    ))

    layout = base_layout('Customer Cohort Retention Matrix')
    layout['xaxis']['tickfont'] = {'color': C['muted']}
    layout['yaxis']['tickfont'] = {'color': C['muted']}
    fig.update_layout(**layout)

    return fig