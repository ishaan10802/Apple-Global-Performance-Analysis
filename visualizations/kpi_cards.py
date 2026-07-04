# visualizations/kpi_cards.py
"""
Reusable KPI card components for the Streamlit dashboard.
All cards follow Apple's dark design language.
Import these functions in app.py to render metric cards.
"""
import streamlit as st


# ── Base card styles ──────────────────────────────────────────────
_CARD_CSS = """
<style>
.kpi-card {
    background: #2C2C2E;
    border-radius: 14px;
    padding: 18px 22px;
    border: 1px solid rgba(255,255,255,0.06);
    height: 100%;
    box-sizing: border-box;
}
.kpi-label {
    color: #98989D;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 0 0 6px 0;
    font-family: -apple-system, sans-serif;
}
.kpi-value {
    color: #F5F5F7;
    font-size: 26px;
    font-weight: 600;
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
    font-family: -apple-system, sans-serif;
}
.kpi-delta-pos {
    color: #30D158;
    font-size: 12px;
    margin: 0;
    font-family: -apple-system, sans-serif;
}
.kpi-delta-neg {
    color: #FF453A;
    font-size: 12px;
    margin: 0;
    font-family: -apple-system, sans-serif;
}
.kpi-delta-neu {
    color: #98989D;
    font-size: 12px;
    margin: 0;
    font-family: -apple-system, sans-serif;
}
.kpi-subtitle {
    color: #6E6E73;
    font-size: 11px;
    margin: 4px 0 0 0;
    font-family: -apple-system, sans-serif;
}
.section-header {
    color: #F5F5F7;
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.3px;
    margin-bottom: 4px;
    font-family: -apple-system, sans-serif;
}
.section-caption {
    color: #98989D;
    font-size: 12px;
    margin-bottom: 16px;
    font-family: -apple-system, sans-serif;
}
.divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 20px 0;
}
.insight-box {
    background: #2C2C2E;
    border-left: 3px solid #0071E3;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 12px 0;
    font-family: -apple-system, sans-serif;
    color: #F5F5F7;
    font-size: 13px;
    line-height: 1.6;
}
.warning-box {
    background: #2C2C2E;
    border-left: 3px solid #FF9F0A;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 12px 0;
    font-family: -apple-system, sans-serif;
    color: #F5F5F7;
    font-size: 13px;
    line-height: 1.6;
}
.alert-box {
    background: #2C2C2E;
    border-left: 3px solid #FF453A;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 12px 0;
    font-family: -apple-system, sans-serif;
    color: #F5F5F7;
    font-size: 13px;
    line-height: 1.6;
}
.success-box {
    background: #2C2C2E;
    border-left: 3px solid #30D158;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 12px 0;
    font-family: -apple-system, sans-serif;
    color: #F5F5F7;
    font-size: 13px;
    line-height: 1.6;
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    font-family: -apple-system, sans-serif;
}
.badge-blue   { background: rgba(0,113,227,0.2);   color: #0071E3; }
.badge-green  { background: rgba(48,209,88,0.2);   color: #30D158; }
.badge-orange { background: rgba(255,159,10,0.2);  color: #FF9F0A; }
.badge-red    { background: rgba(255,69,58,0.2);   color: #FF453A; }
.badge-gray   { background: rgba(110,110,115,0.2); color: #98989D; }
</style>
"""


def inject_styles():
    """Call once at the top of each Streamlit page to inject CSS."""
    st.markdown(_CARD_CSS, unsafe_allow_html=True)


def kpi_card(label: str,
             value: str,
             delta: float = None,
             delta_suffix: str = "%",
             subtitle: str = None):
    """
    Standard KPI metric card.

    Parameters:
        label        Title shown above the value (e.g. "Total Revenue")
        value        Formatted value string (e.g. "$124.3B")
        delta        Numeric change (positive = green, negative = red, None = no badge)
        delta_suffix Text appended to delta (e.g. "%" or " pp")
        subtitle     Optional small text below the delta
    """
    if delta is not None:
        if delta > 0:
            delta_html = (f'<p class="kpi-delta-pos">'
                          f'▲ {abs(delta):.1f}{delta_suffix}</p>')
        elif delta < 0:
            delta_html = (f'<p class="kpi-delta-neg">'
                          f'▼ {abs(delta):.1f}{delta_suffix}</p>')
        else:
            delta_html = (f'<p class="kpi-delta-neu">'
                          f'→ {abs(delta):.1f}{delta_suffix}</p>')
    else:
        delta_html = ""

    sub_html = (f'<p class="kpi-subtitle">{subtitle}</p>'
                if subtitle else "")

    st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-label">{label}</p>
            <p class="kpi-value">{value}</p>
            {delta_html}
            {sub_html}
        </div>
    """, unsafe_allow_html=True)


def kpi_card_mini(label: str, value: str, color: str = "#0071E3"):
    """Compact single-line KPI for dense layouts."""
    st.markdown(f"""
        <div style="background:#2C2C2E;border-radius:10px;
                    padding:12px 16px;border:1px solid rgba(255,255,255,0.06)">
            <span style="color:#98989D;font-size:11px;
                         text-transform:uppercase;letter-spacing:0.5px">
                {label}
            </span>
            <span style="color:{color};font-size:18px;font-weight:600;
                         margin-left:12px;letter-spacing:-0.3px">
                {value}
            </span>
        </div>
    """, unsafe_allow_html=True)


def section_header(title: str, caption: str = ""):
    """Styled section header above a chart group."""
    st.markdown(f"""
        <p class="section-header">{title}</p>
        <p class="section-caption">{caption}</p>
    """, unsafe_allow_html=True)


def divider():
    """Apple-style horizontal rule."""
    st.markdown('<hr class="divider">', unsafe_allow_html=True)


def insight_box(text: str):
    """Blue left-border insight callout box."""
    st.markdown(f'<div class="insight-box">{text}</div>',
                unsafe_allow_html=True)


def warning_box(text: str):
    """Orange left-border warning callout box."""
    st.markdown(f'<div class="warning-box">⚠️ {text}</div>',
                unsafe_allow_html=True)


def alert_box(text: str):
    """Red left-border alert callout box."""
    st.markdown(f'<div class="alert-box">🔴 {text}</div>',
                unsafe_allow_html=True)


def success_box(text: str):
    """Green left-border success callout box."""
    st.markdown(f'<div class="success-box">✅ {text}</div>',
                unsafe_allow_html=True)


def badge(text: str, color: str = "blue") -> str:
    """Return HTML badge string. Colors: blue, green, orange, red, gray."""
    return f'<span class="badge badge-{color}">{text}</span>'


def kpi_row_4(metrics: list):
    """
    Render 4 KPI cards in a row.

    Pass a list of dicts, each with keys:
        label, value, delta (optional), delta_suffix (optional), subtitle (optional)

    Example:
        kpi_row_4([
            {"label": "Revenue", "value": "$124B", "delta": 4.1},
            {"label": "Services", "value": "$26.3B", "delta": 13.9},
            {"label": "Margin", "value": "46.9%", "delta": 1.0, "delta_suffix": " pp"},
            {"label": "TTM", "value": "$416B"},
        ])
    """
    cols = st.columns(4)
    for i, m in enumerate(metrics[:4]):
        with cols[i]:
            kpi_card(
                label        = m.get("label", ""),
                value        = m.get("value", ""),
                delta        = m.get("delta", None),
                delta_suffix = m.get("delta_suffix", "%"),
                subtitle     = m.get("subtitle", None),
            )


def kpi_row_3(metrics: list):
    """Render 3 KPI cards in a row."""
    cols = st.columns(3)
    for i, m in enumerate(metrics[:3]):
        with cols[i]:
            kpi_card(
                label        = m.get("label", ""),
                value        = m.get("value", ""),
                delta        = m.get("delta", None),
                delta_suffix = m.get("delta_suffix", "%"),
                subtitle     = m.get("subtitle", None),
            )


def kpi_row_2(metrics: list):
    """Render 2 KPI cards in a row."""
    cols = st.columns(2)
    for i, m in enumerate(metrics[:2]):
        with cols[i]:
            kpi_card(
                label        = m.get("label", ""),
                value        = m.get("value", ""),
                delta        = m.get("delta", None),
                delta_suffix = m.get("delta_suffix", "%"),
                subtitle     = m.get("subtitle", None),
            )


def progress_bar(label: str, value: float,
                 max_value: float = 100.0,
                 color: str = "#0071E3"):
    """
    Custom styled progress bar.
    value and max_value should be same units (e.g. both billions).
    """
    pct = min(100.0, (value / max_value * 100)) if max_value else 0
    st.markdown(f"""
        <div style="margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;
                        margin-bottom:4px">
                <span style="color:#98989D;font-size:12px">{label}</span>
                <span style="color:#F5F5F7;font-size:12px;font-weight:600">
                    {value:,.1f}
                </span>
            </div>
            <div style="background:#3A3A3C;border-radius:4px;height:6px">
                <div style="background:{color};width:{pct:.1f}%;
                            height:6px;border-radius:4px;
                            transition:width 0.3s ease"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def data_table_header(columns: list):
    """Render styled table column headers."""
    cols = st.columns(len(columns))
    for i, col in enumerate(columns):
        with cols[i]:
            st.markdown(
                f'<p style="color:#98989D;font-size:11px;'
                f'text-transform:uppercase;letter-spacing:0.5px;'
                f'margin:0;padding-bottom:6px;">{col}</p>',
                unsafe_allow_html=True
            )


def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Large page title block used at top of each Streamlit page."""
    st.markdown(f"""
        <div style="padding:8px 0 20px 0;
                    border-bottom:1px solid rgba(255,255,255,0.06);
                    margin-bottom:24px">
            <h1 style="color:#F5F5F7;font-size:28px;font-weight:700;
                       letter-spacing:-0.5px;margin:0;
                       font-family:-apple-system,sans-serif">
                {icon} {title}
            </h1>
            <p style="color:#98989D;font-size:13px;margin:6px 0 0 0;
                      font-family:-apple-system,sans-serif">
                {subtitle}
            </p>
        </div>
    """, unsafe_allow_html=True)