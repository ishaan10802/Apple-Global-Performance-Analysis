# genai/insight_engine.py
"""
Insight Engine — Automated Business Intelligence via GPT-4o.

Three public functions used by app.py:
  generate_insight()    → executive quarterly commentary
  answer_question(q)    → plain English Q&A about the data
  get_kpis()            → raw KPI dict (used by narrative_writer too)
"""
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics.db_connector import query
from genai.config_ai import get_openai_client, MODEL, MAX_TOKENS, TEMP_PROSE, TEMP_FACTS


# ─────────────────────────────────────────────────────────────────
# Schema context sent to GPT-4o for SQL generation
#
# NOTE: this constant is currently unused anywhere in this file — neither
# generate_insight() nor answer_question() reference it. Either wire it into
# a future text-to-SQL path, or remove it so the file doesn't imply
# behavior that doesn't exist. Leaving as-is for now since it may be used
# elsewhere (e.g. narrative_writer.py).
# ─────────────────────────────────────────────────────────────────
_SCHEMA = """
PostgreSQL database: apple_intelligence

VIEWS:
vw_executive_summary — fiscal_year, fiscal_quarter, quarter_label,
  total_revenue_millions, services_revenue_millions, iphone_revenue_millions,
  blended_gross_margin_pct, services_mix_pct, qoq_growth_pct, ttm_revenue_millions

vw_product_margin — fiscal_year, fiscal_quarter, quarter_label,
  product_name (iPhone/Mac/iPad/Wearables & Home/Services/Accessories),
  product_category (Hardware/Services),
  revenue_usd_millions, gross_profit_usd_millions, gross_margin_pct,
  units_millions, revenue_mix_pct

vw_regional_kpi — fiscal_year, fiscal_quarter, quarter_label,
  region_name (Americas/Europe/China/Japan/Rest of Asia Pacific),
  revenue_usd_millions, region_share_pct, qoq_growth_pct, avg_margin_pct

vw_services_growth — fiscal_year, fiscal_quarter, quarter_label,
  services_rev_m, services_margin_pct, services_attach_rate_pct,
  services_qoq_growth_pct

vw_yoy_revenue — fiscal_year, fiscal_quarter, quarter_label,
  product_name, region_name, revenue_usd_millions, yoy_growth_pct

TABLES:
fact_customer — customer_id, first_purchase_date, last_purchase_date,
  total_revenue_usd, total_orders, region_key, segment_key,
  cohort_quarter, is_subscriber (boolean), rfm_score (3-15), clv_estimated_usd

dim_customer_segment — segment_key, segment_name, rfm_tier, revenue_band
dim_region — region_key, region_name
dim_product — product_key, product_name, product_category
"""


def get_kpis() -> dict:
    """Pull all headline KPIs needed for insight generation."""
    exec_df = query("""
        SELECT * FROM vw_executive_summary
        ORDER BY fiscal_year DESC, fiscal_quarter DESC LIMIT 3
    """)
    svc_df = query("""
        SELECT * FROM vw_services_growth
        ORDER BY fiscal_year DESC, fiscal_quarter DESC LIMIT 1
    """)
    prod_df = query("""
        SELECT product_name, revenue_usd_millions,
               gross_margin_pct, revenue_mix_pct
        FROM vw_product_margin
        WHERE fiscal_year=(SELECT MAX(fiscal_year) FROM dim_date)
          AND fiscal_quarter=(SELECT MAX(fiscal_quarter) FROM dim_date
              WHERE fiscal_year=(SELECT MAX(fiscal_year) FROM dim_date))
        ORDER BY revenue_usd_millions DESC
    """)
    reg_df = query("""
        SELECT region_name, revenue_usd_millions,
               region_share_pct, qoq_growth_pct
        FROM vw_regional_kpi
        WHERE fiscal_year=(SELECT MAX(fiscal_year) FROM dim_date)
          AND fiscal_quarter=(SELECT MAX(fiscal_quarter) FROM dim_date
              WHERE fiscal_year=(SELECT MAX(fiscal_year) FROM dim_date))
        ORDER BY revenue_usd_millions DESC
    """)
    cur = exec_df.iloc[0].to_dict() if len(exec_df) > 0 else {}
    return {
        "quarter":    cur.get("quarter_label", "Latest"),
        "total_rev":  round(cur.get("total_revenue_millions", 0), 1),
        "services_m": round(cur.get("services_revenue_millions", 0), 1),
        "margin":     round(cur.get("blended_gross_margin_pct", 0), 1),
        "svc_mix":    round(cur.get("services_mix_pct", 0), 1),
        "qoq":        round(cur.get("qoq_growth_pct", 0) or 0, 1),
        "ttm":        round(cur.get("ttm_revenue_millions", 0), 1),
        "attach":     round(
            svc_df["services_attach_rate_pct"].iloc[0], 1
        ) if len(svc_df) > 0 else 0,
        "products":   prod_df.to_dict("records"),
        "regions":    reg_df.to_dict("records"),
    }


# ─────────────────────────────────────────────────────────────────
# Formatting helpers — every number that reaches the LLM goes through
# one of these, so formatting is consistent and a single None/NULL
# metric can't crash prompt construction or produce something like
# "143.76billion" or "42.6237.81" in the generated prose.
# ─────────────────────────────────────────────────────────────────
def _fmt_billions(value_millions) -> str:
    """Format a $M figure as '$143.76 billion'. Null-safe."""
    if value_millions is None:
        return "$0.00 billion"
    return f"${float(value_millions) / 1000:.2f} billion"


def _fmt_pct(value, decimals: int = 1) -> str:
    """Format a numeric percentage as '47.0%'. Null-safe."""
    if value is None:
        return "N/A"
    return f"{float(value):.{decimals}f}%"


def generate_insight(kpis: dict = None) -> str:
    """
    Send live KPI data to GPT-4o.
    Returns a 3-4 paragraph executive quarterly commentary.
    """
    client = get_openai_client()
    if kpis is None:
        kpis = get_kpis()

    system = """You are a Senior Strategy Consultant at McKinsey preparing a board-ready executive briefing for Apple's Board of Directors.

Requirements:
- Write professional executive business English.
- Return PLAIN TEXT only.
- Do NOT use Markdown.
- Do NOT use backticks (`).
- Do NOT use inline code formatting.
- Do NOT use fenced code blocks.
- Do NOT use HTML.
- Do NOT use bullet lists.
- Write 4 concise paragraphs.
- Always format money as "$143.76 billion".
- Never concatenate numbers together.
- Never repeat the same KPI twice.
- Explain the business implication of every KPI.
- Do not invent facts beyond the supplied data.
"""

    products_str = "\n".join(
        f"- {p['product_name']}: {_fmt_billions(p.get('revenue_usd_millions'))} "
        f"(Margin {_fmt_pct(p.get('gross_margin_pct'))}, "
        f"Mix {_fmt_pct(p.get('revenue_mix_pct'))})"
        for p in kpis["products"]
    )
    regions_str = "\n".join(
        f"- {r['region_name']}: {_fmt_billions(r.get('revenue_usd_millions'))} "
        f"(Share {_fmt_pct(r.get('region_share_pct'))}, "
        f"QoQ {_fmt_pct(r.get('qoq_growth_pct'))})"
        for r in kpis["regions"]
    )
    user = f"""
You are preparing a board-ready executive briefing for Apple.

Use ONLY the KPI values provided below.

Rules:
- Do not invent any numbers.
- Do not repeat numbers.
- Do not merge two different KPIs into one sentence.
- Do not perform calculations.
- Do not infer missing values.
- Return plain text only.
- Write exactly four paragraphs.

KPI DATA (JSON):

{json.dumps(kpis, indent=2)}

Write the executive commentary now.
"""

    resp = client.chat.completions.create(
        model=MODEL, max_tokens=MAX_TOKENS, temperature=TEMP_PROSE,
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}]
    )
    insight = resp.choices[0].message.content.strip()

    # Auto-save
    _save_narrative(insight, kpis["quarter"], "executive_insight")
    return insight


def answer_question(question: str) -> str:
    """
    Natural-language Q&A against the Apple Global Performance Analysis warehouse.
    """
    client = get_openai_client()

    exec_df = query("""
        SELECT *
        FROM vw_executive_summary
        ORDER BY fiscal_year, fiscal_quarter
    """)

    # NOTE: this queries `vw_ai_revenue`, which isn't listed in the _SCHEMA
    # block above (that documents vw_product_margin for product-level data).
    # Confirm this view exists with these exact columns in your live DB —
    # if it was renamed or never created, this call will throw. Worth
    # pointing this at vw_product_margin instead, if vw_ai_revenue was a
    # one-off view that didn't make it into the documented schema.
    product_df = query("""
        SELECT
            fiscal_year,
            fiscal_quarter,
            quarter_label,
            product_name,
            revenue_m
        FROM vw_ai_revenue
        ORDER BY fiscal_year, fiscal_quarter
    """)

    region_df = query("""
        SELECT
            fiscal_year,
            fiscal_quarter,
            quarter_label,
            region_name,
            revenue_usd_millions,
            region_share_pct,
            qoq_growth_pct
        FROM vw_regional_kpi
        ORDER BY fiscal_year, fiscal_quarter
    """)

    services_df = query("""
        SELECT *
        FROM vw_services_growth
        ORDER BY fiscal_year, fiscal_quarter
    """)

    data_str = f"""
EXECUTIVE SUMMARY
{exec_df.to_string(index=False)}

PRODUCT REVENUE
{product_df.to_string(index=False)}

REGIONAL PERFORMANCE
{region_df.to_string(index=False)}

SERVICES PERFORMANCE
{services_df.to_string(index=False)}
"""

    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=800,
        temperature=TEMP_FACTS,
        messages=[
            {
                "role": "system",
                "content": """
You are a Senior Apple Financial Analyst.

Rules:
1. Use ONLY supplied data.
2. Never invent values.
3. Never estimate.
4. Return all quarters when requested.
5. Use markdown tables if user requests data.
6. Mention exact fiscal years and quarters.
7. Use billions when discussing large revenues.
"""
            },
            {
                "role": "user",
                "content": f"""
DATA:

{data_str}

QUESTION:

{question}
"""
            }
        ]
    )

    return resp.choices[0].message.content.strip()


def _save_narrative(text: str, quarter: str, prefix: str) -> str:
    """Save generated text to exports/ai_narratives/."""
    out_dir = os.path.join(
        os.path.dirname(__file__), '..', 'exports', 'ai_narratives'
    )
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"{prefix}_{ts}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Apple Global Performance Analysis — {prefix.replace('_',' ').title()}\n")
        f.write(f"Quarter: {quarter}\n")
        f.write(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(text)
    return path


if __name__ == "__main__":
    print("Testing insight engine...")
    insight = generate_insight()
    print("\n" + "─" * 60)
    print(insight)