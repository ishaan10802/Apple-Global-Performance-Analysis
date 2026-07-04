# analytics/rfm_analysis.py

import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from analytics.db_connector import query


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_customer_data():
    """
    Load customer data together with the official
    RFM segment stored in PostgreSQL.
    """

    sql = """
    SELECT
        f.customer_id,
        f.first_purchase_date,
        f.last_purchase_date,
        f.total_orders,
        f.total_revenue_usd,
        f.clv_estimated_usd,
        f.is_subscriber,
        f.rfm_score,
        f.cohort_quarter,
        r.region_name,
        s.segment_name
    FROM fact_customer f
    JOIN dim_region r
        ON f.region_key = r.region_key
    JOIN dim_customer_segment s
        ON f.segment_key = s.segment_key
    """

    return query(sql)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

def rfm_summary(df):
    """
    Generate RFM segment summary using the official customer segments
    stored in PostgreSQL.

    Returns
    -------
    pd.DataFrame
        Segment-level KPI summary exported to CSV.
    """

    # -----------------------------
    # Segment-level KPIs
    # -----------------------------
    summary = (
        df.groupby("segment_name")
        .agg(
            customers=("customer_id", "count"),
            avg_revenue=("total_revenue_usd", "mean"),
            median_revenue=("total_revenue_usd", "median"),
            total_rev=("total_revenue_usd", "sum"),
            avg_orders=("total_orders", "mean"),
            avg_clv=("clv_estimated_usd", "mean"),
            subscriber_pct=("is_subscriber", "mean"),
        )
        .round(2)
        .reset_index()
    )

    # -----------------------------
    # Additional KPIs
    # -----------------------------
    summary["subscriber_pct"] = (
        summary["subscriber_pct"] * 100
    ).round(2)

    summary["rev_share_pct"] = (
        summary["total_rev"]
        / summary["total_rev"].sum()
        * 100
    ).round(2)

    summary["clv_share_pct"] = (
        summary["avg_clv"] * summary["customers"]
        / (summary["avg_clv"] * summary["customers"]).sum()
        * 100
    ).round(2)
    

    # -----------------------------
    # Better formatting
    # -----------------------------
    summary["avg_revenue"] = summary["avg_revenue"].round(0)
    summary["median_revenue"] = summary["median_revenue"].round(0)
    summary["avg_clv"] = summary["avg_clv"].round(0)
    summary["avg_orders"] = summary["avg_orders"].round(1)

    # -----------------------------
    # Business-friendly segment order
    # -----------------------------
    order = [
        "Champions",
        "Loyal Customers",
        "Potential Loyalists",
        "Promising",
        "New Customers",
        "Needs Attention",
        "At Risk",
        "Lost Customers",
    ]

    summary["segment_name"] = pd.Categorical(
        summary["segment_name"],
        categories=order,
        ordered=True,
    )

    summary = (
        summary.sort_values("segment_name")
        .reset_index(drop=True)
    )

    # -----------------------------
    # Validation
    # -----------------------------
    if summary.empty:
        raise ValueError("RFM summary is empty.")

    # -----------------------------
    # Export
    # -----------------------------
    os.makedirs(
        "../data/processed",
        exist_ok=True,
    )

    summary.to_csv(
        "../data/processed/rfm_results.csv",
        index=False,
    )

    # Export detailed customer dataset
    df.to_csv(
        "../data/processed/rfm_detail.csv",
        index=False,
    )

    # -----------------------------
    # Logging
    # -----------------------------
    print(f"✓ RFM Summary Generated ({len(summary)} segments)")
    print("✓ Exported: rfm_results.csv")
    print("✓ Exported: rfm_detail.csv")

    return summary   

# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def run_rfm():

    df = load_customer_data()

    if df.empty:
     raise ValueError("fact_customer table is empty.")

    if df["customer_id"].duplicated().any():
     raise ValueError("Duplicate customer IDs found.")

    if df["segment_name"].isna().any():
     raise ValueError("Some customers have no segment assigned.")


    summary = rfm_summary(df)

    return {
        "detail": df,
        "summary": summary
    }


if __name__ == "__main__":

    result = run_rfm()

    print(
        result["summary"].to_string(index=False)
    )