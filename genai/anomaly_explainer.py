# genai/anomaly_explainer.py
"""
Anomaly Detection + GPT-4o Explanation Engine.

Scans revenue data for statistically unusual patterns
using z-score analysis, then asks GPT-4o to explain
each anomaly in real-world business context.

Output: text report ✅ Executive brief generated successfully.
"""
import os
import sys
import json
from datetime import datetime

import pandas as pd
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics.db_connector import query
from genai.config_ai import get_openai_client, MODEL, TEMP_FACTS


def detect_revenue_anomalies(z_threshold: float = 1.8) -> list:
    """
    Flag product-quarters where YoY growth is statistically unusual.

    Method: z-score per product across all available quarters.
    Quarters with |z| > z_threshold are flagged as anomalies.

    Returns list of dicts sorted by severity (highest |z| first).
    """
    df = query("""
        SELECT quarter_label, fiscal_year, fiscal_quarter,
               product_name, region_name,
               revenue_usd_millions, yoy_growth_pct
        FROM vw_yoy_revenue
        WHERE yoy_growth_pct IS NOT NULL
        ORDER BY fiscal_year, fiscal_quarter
    """)

    anomalies = []

    for product in df["product_name"].unique():
        sub = df[df["product_name"] == product].copy()
        if len(sub) < 5:
            continue

        # Aggregate across regions for product-level signal
        agg = sub.groupby(
            ["fiscal_year", "fiscal_quarter", "quarter_label"]
        )["yoy_growth_pct"].mean().reset_index()

        mean = agg["yoy_growth_pct"].mean()
        std  = agg["yoy_growth_pct"].std()
        if std == 0 or pd.isna(std):
            continue

        agg["z"] = (agg["yoy_growth_pct"] - mean) / std
        flagged   = agg[agg["z"].abs() > z_threshold]

        for _, row in flagged.iterrows():
            direction = "spike"   if row["z"] > 0 else "decline"
            severity  = "Critical" if abs(row["z"]) > 3 else \
                        "High"     if abs(row["z"]) > 2.5 else "Medium"
            anomalies.append({
                "quarter":    row["quarter_label"],
                "fiscal_year":row["fiscal_year"],
                "fiscal_q":   row["fiscal_quarter"],
                "product":    product,
                "yoy_growth": round(row["yoy_growth_pct"], 1),
                "z_score":    round(row["z"], 2),
                "direction":  direction,
                "severity":   severity,
            })

    # Sort by absolute z-score descending
    anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
    return anomalies[:12]


def explain_anomaly(anomaly: dict, client) -> str:
    """
    Ask GPT-4o to explain one anomaly in business context.
    Response is 2-3 sentences referencing real Apple events.
    """
    resp = client.chat.completions.create(
        model=MODEL, max_tokens=250, temperature=TEMP_FACTS,
        messages=[
            {"role": "system",
             "content": (
                 """
You are a financial analytics specialist.

Use ONLY the anomaly information provided.

Rules:
1. Do not invent Apple events.
2. Do not reference product launches unless supplied.
3. Do not reference macroeconomic events unless supplied.
4. Provide plausible business interpretations only.
5. Clearly distinguish fact from interpretation.
6. Maximum 3 sentences.
"""
             )},
            {"role": "user",
             "content": (
                 f"Product: {anomaly['product']}\n"
                 f"Quarter: {anomaly['quarter']}\n"
                 f"YoY Growth: {anomaly['yoy_growth']}% "
                 f"(z-score: {anomaly['z_score']})\n"
                 f"Type: Unusual revenue {anomaly['direction']}\n\n"
                 """
Provide a business interpretation for this anomaly.

Use only the supplied information.
Avoid unsupported assumptions.
"""
             )}
        ]
    )
    return resp.choices[0].message.content.strip()


def run_anomaly_report() -> list:
    """
    Full pipeline: detect anomalies, get GPT-4o explanations,
    save report to exports/ai_narratives/.
    Returns list of anomaly dicts with explanations added.
    """
    print("Scanning revenue data for anomalies...")
    anomalies = detect_revenue_anomalies()

    if not anomalies:
        print("No significant anomalies detected.")
        return []

    print(f"Found {len(anomalies)} anomalies. Generating explanations...\n")
    client  = get_openai_client()
    results = []

    for i, anom in enumerate(anomalies, 1):
        label = f"{anom['product']} — {anom['quarter']}"
        print(f"  [{i}/{len(anomalies)}] {label}")
        explanation       = explain_anomaly(anom, client)
        anom["explanation"] = explanation  
        results.append(anom)
        print(f"     {explanation[:80]}...")

    # Save report
    out_dir = os.path.join(
        os.path.dirname(__file__), '..', 'exports', 'ai_narratives'
    )
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"anomaly_report_{ts}.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write("Apple Global Performance Analysis — ANOMALY DETECTION REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%B %d, %Y')}\n")
        f.write(f"Anomalies detected: {len(results)}\n")
        f.write("=" * 60 + "\n\n")

        for a in results:
            sev_symbol = {"Critical":"🔴","High":"🟠","Medium":"🟡"}.get(
                a["severity"], "⚪"
            )
            f.write(f"{sev_symbol} [{a['severity'].upper()}] "
                    f"{a['product']} — {a['quarter']}\n")
            f.write(f"  YoY Growth : {a['yoy_growth']:+.1f}%\n")
            f.write(f"  Z-Score    : {a['z_score']:.2f}\n")
            f.write(f"  Type       : {a['direction'].capitalize()}\n")
            f.write(f"  Explanation:\n  {a['explanation']}\n")
            f.write("─" * 50 + "\n\n")

    print(f"\n✅ Anomaly report saved: {path}")
    return results


def get_anomaly_summary_for_app() -> list:
    """
    Lightweight version for the Streamlit app.
    Returns anomalies WITHOUT calling GPT-4o (for fast loading).
    Call run_anomaly_report() for full AI explanations.
    """
    return detect_revenue_anomalies()


if __name__ == "__main__":
    results = run_anomaly_report()
    print(f"\nTotal anomalies explained: {len(results)}")