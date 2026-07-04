# check_database.py
# Run: python check_database.py
# This tells you EXACTLY what is wrong before you fix anything.

import psycopg2

DB = {"host":"localhost","port":5432,"database":"apple_intelligence",
      "user":"postgres","password":"Ishaan@01"}

try:
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    print("=" * 60)
    print("  DATABASE DIAGNOSTIC REPORT")
    print("=" * 60)

    # Table row counts
    tables = ["dim_date","dim_product","dim_region",
              "dim_customer_segment","fact_revenue","fact_customer"]
    print("\n── Table Row Counts ──────────────────────────────────")
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t:<30} {cur.fetchone()[0]:>8,} rows")
        except Exception as e:
            print(f"  {t:<30} ERROR: {e}")

    # Revenue check — should be ~143,756 for FY2026 Q1
    print("\n── Revenue Check (last 4 quarters) ──────────────────")
    try:
        cur.execute("""
            SELECT d.quarter_label,
                   ROUND(SUM(f.revenue_usd_millions),0) AS total_rev
            FROM fact_revenue f
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY d.quarter_label, d.fiscal_year, d.fiscal_quarter
            ORDER BY d.fiscal_year DESC, d.fiscal_quarter DESC
            LIMIT 4
        """)
        rows = cur.fetchall()
        for row in rows:
            flag = " ← 2x DUPLICATED!" if row[1] > 160000 else " ✓"
            print(f"  {row[0]:<15} ${row[1]:>12,.0f}M{flag}")
        print("\n  Expected FY2026 Q1: ~$143,756M")
        print("  Expected FY2025 Q4: ~$102,466M")
    except Exception as e:
        print(f"  View error: {e}")

    # Duplicate check
    print("\n── Duplicate Row Check ───────────────────────────────")
    try:
        cur.execute("""
            SELECT date_key, product_key, region_key, COUNT(*) AS cnt
            FROM fact_revenue
            GROUP BY date_key, product_key, region_key
            HAVING COUNT(*) > 1
            LIMIT 3
        """)
        dups = cur.fetchall()
        if dups:
            print(f"  ⛔  DUPLICATES FOUND: {len(dups)} combinations have >1 row")
            print("  This is your 2x revenue bug. Run nuclear_reset.py next.")
        else:
            print("  ✓  No duplicates found in fact_revenue")
    except Exception as e:
        print(f"  Error: {e}")

    conn.close()
    print("\n" + "=" * 60)

except Exception as e:
    print(f"\n⛔  CANNOT CONNECT: {e}")
    print("   Check your PostgreSQL service is running")
    print("   Verify password in this script matches your setup")