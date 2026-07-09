# genai/narrative_writer.py
"""
Executive Narrative Writer.
Generates a complete multi-section written report from live data.
Output: formatted text file ✅ Executive brief generated successfully.

Sections:
  1. Financial Summary
  2. Services Business Analysis
  3. Customer Intelligence
  4. Geographic Risk Assessment
  5. Strategic Outlook
"""
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics.db_connector import query
from genai.config_ai import get_openai_client, MODEL, TEMP_PROSE
from genai.insight_engine import get_kpis


def _fetch_customer_summary() -> dict:
    """Pull synthetic customer segment data for narrative generation."""

    seg_df = query("""
        SELECT ds.segment_name,
               COUNT(*)                                      AS customers,
               ROUND(AVG(fc.total_revenue_usd)::numeric, 0) AS avg_rev,
               ROUND(SUM(fc.total_revenue_usd)::numeric / 1e6, 2) AS total_rev_m,
               ROUND(AVG(fc.clv_estimated_usd)::numeric, 0) AS avg_clv,
               SUM(CASE WHEN fc.is_subscriber THEN 1 ELSE 0 END) AS subscribers
        FROM fact_customer fc
        JOIN dim_customer_segment ds
            ON fc.segment_key = ds.segment_key
        GROUP BY ds.segment_name
        ORDER BY total_rev_m DESC
    """)

    total_clv = query("""
        SELECT
            ROUND(SUM(clv_estimated_usd)/1e9::numeric, 2) AS clv
        FROM fact_customer
    """)

    return {
        "segments": seg_df.to_dict("records"),
        "total_clv": float(total_clv["clv"].iloc[0])
    }


def _write_section(section_key: str,
                   kpis: dict,
                   customer: dict,
                   client) -> str:
    """Write one report section using GPT-4o."""
    prompts = {
        "financial_summary": (
            f"Write the FINANCIAL SUMMARY section (3 paragraphs).\n"
            f"Revenue: ${kpis['total_rev']}M | QoQ: {kpis['qoq']}% | "
            f"TTM: ${kpis['ttm']}M | Blended Margin: {kpis['margin']}%\n"
            f"Products: {json.dumps(kpis['products'])}\n"
            "Lead with total revenue. Discuss margin expansion. "
            "End with TTM trajectory."
        ),
        "services_analysis": (
            f"Write the SERVICES BUSINESS ANALYSIS section (2 paragraphs).\n"
            f"Services Revenue: ${kpis['services_m']}M | "
            f"Mix: {kpis['svc_mix']}% | Attach Rate: {kpis['attach']}%\n"
            "Explain the strategic importance of Services attach rate. "
            "Quantify the margin premium of Services (~75%) vs Hardware (~37%). "
            "Explain what growing Services mix means for blended margin."
        ),

        "customer_intelligence": (
            f"Write the SYNTHETIC CUSTOMER INTELLIGENCE section (2 paragraphs).\n"
            f"Segments: {json.dumps(customer['segments'][:4])}\n"
            f"Total CLV portfolio: ${customer['total_clv']}B\n"
            "Discuss revenue concentration across customer segments. "
            "Highlight the role of Champions and Loyal Customers. "
            "Reference CLV portfolio value. "
            "Do not discuss churn rates."
        ),
        
        "geographic_risks": (
            f"Write the GEOGRAPHIC RISK ASSESSMENT section (2 paragraphs).\n"
            f"Regions: {json.dumps(kpis['regions'])}\n"
            "Lead with Americas dominance. Address China share decline "
            "from 19% (FY2022) to 15.5% (FY2025) explicitly. "
            "Identify high-growth markets."
        ),
        "strategic_outlook": (
            f"Write the STRATEGIC OUTLOOK section (2 paragraphs).\n"
            f"Current quarter: {kpis['quarter']} | Revenue: ${kpis['total_rev']}M\n"
            "Discuss: Apple Intelligence / AI integration, Services growth runway, "
            "iPhone 17 cycle, Vision Pro positioning, China risk mitigation. "
            "End with a single forward-looking guidance sentence."
        ),
    }
    prompt = prompts.get(section_key, "Write a business analysis section.")
    resp = client.chat.completions.create(
        model=MODEL, max_tokens=500, temperature=TEMP_PROSE,
        messages=[
            {"role": "system",
             "content": (
                 "You are the Director of FP&A at Apple Inc writing "
                 "a formal business review document. Write in formal "
                 "business English. Every claim must reference the "
                 "specific data provided. No filler. Dense with insight."
             )},
            {"role": "user", "content": prompt}
        ]
    )
    return resp.choices[0].message.content.strip()


def generate_full_narrative() -> str:
    """
    Generate a complete five-section executive report narrative.
    Pulls live data for every section. Saves to exports/ai_narratives/.
    Returns the full text string.
    """
    print("Fetching data for narrative generation...")
    kpis     = get_kpis()
    customer = _fetch_customer_summary()
    client   = get_openai_client()

    sections = [
        ("financial_summary",    "1. Financial Summary"),
        ("services_analysis",    "2. Services Business Analysis"),
        ("customer_intelligence","3. Synthetic Customer Intelligence"),
        ("geographic_risks",     "4. Geographic Risk Assessment"),
        ("strategic_outlook",    "5. Strategic Outlook"),
    ]

    parts = [
        "═" * 64,
        "Apple Global Performance Analysis PLATFORM",
        "Executive Quarterly Business Review",
        f"Quarter: {kpis['quarter']}",
        f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}",
        f"Data source: Apple SEC filings (8-K / 10-K / 10-Q)",
        "═" * 64,
        "",
    ]

    for key, title in sections:
        print(f"  Writing: {title}...")
        text = _write_section(key, kpis, customer, client)
        parts.append(f"\n{title.upper()}")
        parts.append("─" * 40)
        parts.append(text)
        parts.append("")

    parts.append("═" * 64)
    parts.append("END OF REPORT")
    parts.append("Source: Apple public financial disclosures + simulated customer data")

    narrative = "\n".join(parts)

    # Save
    out_dir = os.path.join(
        os.path.dirname(__file__), '..', 'exports', 'ai_narratives'
    )
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"full_narrative_{ts}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(narrative)

    print(f"\n✅ Narrative saved: {path}")
    print(f"   Length: {len(narrative):,} characters")
    return narrative


if __name__ == "__main__":
    narrative = generate_full_narrative()
    print("\nPREVIEW (first 600 chars):")
    print("─" * 60)
    print(narrative[:600])
    print("...")