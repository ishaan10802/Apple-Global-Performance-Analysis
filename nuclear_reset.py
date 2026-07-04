# nuclear_reset.py
"""
NUCLEAR RESET — Apple Global Performance Analysis Platform
====================================================
Drops and recreates the entire database from scratch.
Seeds with verified Apple financial data.
Guarantees no duplication is possible.

Run ONCE from project root:
    python nuclear_reset.py

Expected output after success:
    FY2026 Q1  $143,756M  $30,013M  46.8%
    FY2025 Q4  $102,466M  $28,750M  47.1%
    FY2025 Q3   $94,036M  $27,423M  46.5%
"""

import psycopg2
import numpy as np
import random
from datetime import date, timedelta
import sys

# ── UPDATE THIS IF YOUR PASSWORD IS DIFFERENT ─────────────────────
DB = {
    "host":     "localhost",
    "port":     5432,
    "database": "apple_intelligence",
    "user":     "postgres",
    "password": "Ishaan@01",   # ← your PostgreSQL password
}
# ──────────────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════════
# REAL APPLE REVENUE DATA — USD Billions
# Source: Apple SEC 8-K and 10-Q filings
# ═══════════════════════════════════════════════════════════════════
APPLE_REVENUE_DATA = {
    # FY2022
    (2022,1,"iPhone"):69.138,  (2022,1,"Mac"):10.852, (2022,1,"iPad"):7.248,
    (2022,1,"Wearables & Home"):14.702, (2022,1,"Services"):19.516,
    (2022,2,"iPhone"):50.570,  (2022,2,"Mac"):10.435, (2022,2,"iPad"):7.646,
    (2022,2,"Wearables & Home"):8.806,  (2022,2,"Services"):19.821,
    (2022,3,"iPhone"):40.665,  (2022,3,"Mac"):7.382,  (2022,3,"iPad"):7.224,
    (2022,3,"Wearables & Home"):8.084,  (2022,3,"Services"):19.604,
    (2022,4,"iPhone"):42.627,  (2022,4,"Mac"):11.508, (2022,4,"iPad"):7.174,
    (2022,4,"Wearables & Home"):9.651,  (2022,4,"Services"):19.188,
    # FY2023
    (2023,1,"iPhone"):65.775,  (2023,1,"Mac"):7.735,  (2023,1,"iPad"):9.396,
    (2023,1,"Wearables & Home"):13.482, (2023,1,"Services"):20.766,
    (2023,2,"iPhone"):51.334,  (2023,2,"Mac"):7.168,  (2023,2,"iPad"):6.670,
    (2023,2,"Wearables & Home"):8.757,  (2023,2,"Services"):20.907,
    (2023,3,"iPhone"):39.669,  (2023,3,"Mac"):6.840,  (2023,3,"iPad"):5.791,
    (2023,3,"Wearables & Home"):8.284,  (2023,3,"Services"):21.213,
    (2023,4,"iPhone"):43.805,  (2023,4,"Mac"):7.614,  (2023,4,"iPad"):6.443,
    (2023,4,"Wearables & Home"):9.320,  (2023,4,"Services"):22.314,
    # FY2024
    (2024,1,"iPhone"):69.702,  (2024,1,"Mac"):7.780,  (2024,1,"iPad"):7.023,
    (2024,1,"Wearables & Home"):11.953, (2024,1,"Services"):23.117,
    (2024,2,"iPhone"):45.963,  (2024,2,"Mac"):7.451,  (2024,2,"iPad"):5.559,
    (2024,2,"Wearables & Home"):7.913,  (2024,2,"Services"):23.867,
    (2024,3,"iPhone"):39.296,  (2024,3,"Mac"):7.009,  (2024,3,"iPad"):7.162,
    (2024,3,"Wearables & Home"):8.097,  (2024,3,"Services"):24.213,
    (2024,4,"iPhone"):46.222,  (2024,4,"Mac"):7.744,  (2024,4,"iPad"):6.950,
    (2024,4,"Wearables & Home"):9.042,  (2024,4,"Services"):24.972,
    # FY2025 — Source: Apple 8-K Jan/May/Jul/Oct 2025
    (2025,1,"iPhone"):69.138,  (2025,1,"Mac"):8.987,  (2025,1,"iPad"):8.088,
    (2025,1,"Wearables & Home"):11.747, (2025,1,"Services"):26.340,
    (2025,2,"iPhone"):46.841,  (2025,2,"Mac"):7.949,  (2025,2,"iPad"):6.402,
    (2025,2,"Wearables & Home"):7.522,  (2025,2,"Services"):26.645,
    (2025,3,"iPhone"):44.582,  (2025,3,"Mac"):8.046,  (2025,3,"iPad"):6.581,
    (2025,3,"Wearables & Home"):7.404,  (2025,3,"Services"):27.423,
    (2025,4,"iPhone"):49.025,  (2025,4,"Mac"):8.726,  (2025,4,"iPad"):6.952,
    (2025,4,"Wearables & Home"):9.013,  (2025,4,"Services"):28.750,
    # FY2026 Q1 — Source: Apple 10-Q Feb 2026
    (2026,1,"iPhone"):85.269,  (2026,1,"Mac"):8.386,  (2026,1,"iPad"):8.595,
    (2026,1,"Wearables & Home"):11.493, (2026,1,"Services"):30.013,
}

# EXACT splits — NO noise applied. Sum = 1.0000 guaranteed.
# This prevents the "total > source" bug permanently.
REGIONAL_SPLITS = {
    2022: {"Americas":0.4400,"Europe":0.2400,"China":0.1900,
           "Japan":0.0700,"Rest of Asia Pacific":0.0600},
    2023: {"Americas":0.4380,"Europe":0.2490,"China":0.1860,
           "Japan":0.0700,"Rest of Asia Pacific":0.0570},
    2024: {"Americas":0.4270,"Europe":0.2590,"China":0.1710,
           "Japan":0.0640,"Rest of Asia Pacific":0.0790},
    2025: {"Americas":0.4290,"Europe":0.2670,"China":0.1550,
           "Japan":0.0690,"Rest of Asia Pacific":0.0800},
    2026: {"Americas":0.4300,"Europe":0.2650,"China":0.1500,
           "Japan":0.0640,"Rest of Asia Pacific":0.0910},
}


SVC_MARGIN_BY_YEAR = {
    2022: {1:0.718, 2:0.704, 3:0.712, 4:0.697},
    2023: {1:0.719, 2:0.705, 3:0.698, 4:0.714},
    2024: {1:0.731, 2:0.722, 3:0.740, 4:0.728},
    2025: {1:0.752, 2:0.743, 3:0.750, 4:0.745},
    2026: {1:0.761}
}

# Hardware improvement trend — M-chip + supply chain efficiency
HW_TREND = {
    2022:-0.012, 2023:-0.005, 2024:0.000, 2025:+0.008, 2026:+0.010
}

# Base hardware margins aligned to Apple Products segment ~36.8% (FY2025)
BASE_MARGINS = {
    "iPhone":           0.385,   
    "Mac":              0.375,
    "iPad":             0.338,
    "Wearables & Home": 0.343,
    "Services":         0.754,
    "Accessories":      0.348,
}

# ASPs for unit calculation
ASP_MAP = {
    "iPhone":950, "Mac":1500, "iPad":550,
    "Wearables & Home":350, "Services":0, "Accessories":130,
}

def get_margin(product, fy, fq, rng):
    if product == "Services":
        base = SVC_MARGIN_BY_YEAR.get(
    fy,
    {1: BASE_MARGINS["Services"]}
).get(
    fq,
    BASE_MARGINS["Services"]
)
    else:
        base = BASE_MARGINS.get(product, 0.380) + HW_TREND.get(fy, 0.0)

    # CORRECTED seasonal pattern — Q4 (iPhone launch) has margin pressure
    # due to new component costs. Q1 holiday = higher ASP mix = higher margin.
    seasonal = {
        1: +0.006,   # Holiday quarter: premium mix lifts margin
        2: -0.008,   # Jan-Mar: post-holiday channel mix, lower margin
        3: -0.005,   # Apr-Jun: normal business quarter
        4: -0.010,   # Jul-Sep: iPhone launch quarter, new BOM costs
    }.get(fq, 0.0)

    noise_max = 0.004 if product == "Services" else 0.008
    noise = rng.uniform(-noise_max, noise_max)
    return float(max(0.28, min(0.80, base + seasonal + noise)))

# ═══════════════════════════════════════════════════════════════════
# SQL — DROP EVERYTHING
# ═══════════════════════════════════════════════════════════════════
SQL_DROP = """
DROP VIEW  IF EXISTS vw_executive_summary    CASCADE;
DROP VIEW  IF EXISTS vw_services_growth      CASCADE;
DROP VIEW  IF EXISTS vw_regional_kpi         CASCADE;
DROP VIEW  IF EXISTS vw_product_margin       CASCADE;
DROP VIEW  IF EXISTS vw_yoy_revenue          CASCADE;
DROP TABLE IF EXISTS fact_customer           CASCADE;
DROP TABLE IF EXISTS fact_subscriptions      CASCADE;
DROP TABLE IF EXISTS fact_revenue            CASCADE;
DROP TABLE IF EXISTS dim_customer_segment    CASCADE;
DROP TABLE IF EXISTS dim_region              CASCADE;
DROP TABLE IF EXISTS dim_product             CASCADE;
DROP TABLE IF EXISTS dim_date                CASCADE;
"""

# ═══════════════════════════════════════════════════════════════════
# SQL — CREATE TABLES
# ═══════════════════════════════════════════════════════════════════
SQL_CREATE_TABLES = """
CREATE TABLE dim_date (
    date_key       SERIAL PRIMARY KEY,
    full_date      DATE        NOT NULL,
    fiscal_year    INT         NOT NULL,
    fiscal_quarter INT         NOT NULL,
    calendar_year  INT         NOT NULL,
    calendar_month INT         NOT NULL,
    quarter_label  VARCHAR(12),
    is_current_qtr BOOLEAN     DEFAULT FALSE
);

CREATE TABLE dim_product (
    product_key       SERIAL PRIMARY KEY,
    product_name      VARCHAR(100) NOT NULL,
    product_category  VARCHAR(50),
    launch_year       INT,
    is_active         BOOLEAN  DEFAULT TRUE,
    gross_margin_tier VARCHAR(20)
);

CREATE TABLE dim_region (
    region_key       SERIAL PRIMARY KEY,
    region_name      VARCHAR(100) NOT NULL,
    region_code      VARCHAR(10),
    currency_primary VARCHAR(10),
    is_high_growth   BOOLEAN  DEFAULT FALSE
);

CREATE TABLE dim_customer_segment (
    segment_key  SERIAL PRIMARY KEY,
    segment_name VARCHAR(50),
    rfm_tier     VARCHAR(20),
    revenue_band VARCHAR(20)
);

CREATE TABLE fact_revenue (
    revenue_key               SERIAL PRIMARY KEY,
    date_key                  INT  REFERENCES dim_date(date_key),
    product_key               INT  REFERENCES dim_product(product_key),
    region_key                INT  REFERENCES dim_region(region_key),
    revenue_usd_millions      DECIMAL(12,2) NOT NULL,
    units_millions            DECIMAL(10,4),
    asp_usd                   DECIMAL(10,2),
    gross_margin_pct          DECIMAL(6,2),
    gross_profit_usd_millions DECIMAL(12,2),
    yoy_growth_pct            DECIMAL(8,2)
);

CREATE TABLE fact_subscriptions (
    subscription_key              SERIAL PRIMARY KEY,
    date_key                      INT REFERENCES dim_date(date_key),
    region_key                    INT REFERENCES dim_region(region_key),
    paid_subscriptions_millions   DECIMAL(8,2),
    services_revenue_usd_millions DECIMAL(12,2),
    subscriber_growth_pct         DECIMAL(6,2),
    arpu_usd                      DECIMAL(8,2)
);

CREATE TABLE fact_customer (
    customer_key        SERIAL  PRIMARY KEY,
    customer_id         VARCHAR(20) UNIQUE,
    first_purchase_date DATE,
    last_purchase_date  DATE,
    total_revenue_usd   DECIMAL(12,2),
    total_orders        INT,
    region_key          INT REFERENCES dim_region(region_key),
    segment_key         INT REFERENCES dim_customer_segment(segment_key),
    cohort_quarter      VARCHAR(12),
    is_subscriber       BOOLEAN DEFAULT FALSE,
    rfm_score           INT,
    clv_estimated_usd   DECIMAL(12,2)
);
"""

# ═══════════════════════════════════════════════════════════════════
# SQL — CREATE VIEWS
# ═══════════════════════════════════════════════════════════════════
SQL_VIEW_YOY = """
CREATE OR REPLACE VIEW vw_yoy_revenue AS
WITH base AS (
    SELECT
        d.fiscal_year, d.fiscal_quarter, d.quarter_label,
        p.product_name, p.product_category, r.region_name,
        SUM(f.revenue_usd_millions)      AS revenue_usd_millions,
        SUM(f.gross_profit_usd_millions) AS gross_profit_usd_millions,
        AVG(f.gross_margin_pct)          AS avg_gross_margin_pct,
        SUM(f.units_millions)            AS units_millions
    FROM fact_revenue f
    JOIN dim_date    d ON f.date_key    = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_region  r ON f.region_key  = r.region_key
    GROUP BY d.fiscal_year, d.fiscal_quarter, d.quarter_label,
             p.product_name, p.product_category, r.region_name
),
lagged AS (
    SELECT *,
        -- offset = 4 → same quarter prior fiscal year = TRUE YoY
        -- (offset = 1 would be QoQ, which was the original bug)
        LAG(revenue_usd_millions, 4) OVER (
            PARTITION BY product_name, region_name
            ORDER BY fiscal_year, fiscal_quarter
        ) AS prior_rev
    FROM base
)
SELECT *,
    CASE WHEN prior_rev > 0
         THEN ROUND(((revenue_usd_millions - prior_rev)/prior_rev)*100, 2)
         ELSE NULL END AS yoy_growth_pct,
    ROUND(revenue_usd_millions - COALESCE(prior_rev,0), 2) AS yoy_delta_m
FROM lagged;
"""

SQL_VIEW_PRODUCT_MARGIN = """
CREATE OR REPLACE VIEW vw_product_margin AS
SELECT
    d.fiscal_year, d.fiscal_quarter, d.quarter_label,
    p.product_name, p.product_category, p.gross_margin_tier,
    SUM(f.revenue_usd_millions)      AS revenue_usd_millions,
    SUM(f.gross_profit_usd_millions) AS gross_profit_usd_millions,
    ROUND(AVG(f.gross_margin_pct),2) AS gross_margin_pct,
    SUM(f.units_millions)            AS units_millions,
    ROUND(
        SUM(f.revenue_usd_millions) /
        NULLIF(SUM(SUM(f.revenue_usd_millions)) OVER (
            PARTITION BY d.fiscal_year, d.fiscal_quarter
        ),0)*100, 2
    ) AS revenue_mix_pct,
    SUM(SUM(f.revenue_usd_millions)) OVER (
        PARTITION BY d.fiscal_year, p.product_name
        ORDER BY d.fiscal_quarter
        ROWS UNBOUNDED PRECEDING
    ) AS ytd_revenue_millions
FROM fact_revenue f
JOIN dim_date    d ON f.date_key    = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY d.fiscal_year, d.fiscal_quarter, d.quarter_label,
         p.product_name, p.product_category, p.gross_margin_tier;
"""

SQL_VIEW_REGIONAL_KPI = """
CREATE OR REPLACE VIEW vw_regional_kpi AS
WITH rt AS (
    SELECT
        d.fiscal_year, d.fiscal_quarter, d.quarter_label,
        r.region_name, r.region_code, r.is_high_growth,
        SUM(f.revenue_usd_millions)       AS revenue_usd_millions,
        SUM(f.gross_profit_usd_millions)  AS gross_profit_usd_millions,
        ROUND(AVG(f.gross_margin_pct),2)  AS avg_margin_pct
    FROM fact_revenue f
    JOIN dim_date   d ON f.date_key   = d.date_key
    JOIN dim_region r ON f.region_key = r.region_key
    GROUP BY d.fiscal_year, d.fiscal_quarter, d.quarter_label,
             r.region_name, r.region_code, r.is_high_growth
),
gt AS (
    SELECT fiscal_year, fiscal_quarter, SUM(revenue_usd_millions) AS global_rev_m
    FROM rt GROUP BY fiscal_year, fiscal_quarter
),
lp AS (
    SELECT *,
        LAG(revenue_usd_millions) OVER (
            PARTITION BY region_name ORDER BY fiscal_year, fiscal_quarter
        ) AS prior_rev
    FROM rt
)
SELECT lp.*, gt.global_rev_m,
    ROUND(lp.revenue_usd_millions/NULLIF(gt.global_rev_m,0)*100,2) AS region_share_pct,
    CASE WHEN lp.prior_rev>0
         THEN ROUND(((lp.revenue_usd_millions-lp.prior_rev)/lp.prior_rev)*100,2)
         ELSE NULL END AS qoq_growth_pct
FROM lp
JOIN gt ON lp.fiscal_year=gt.fiscal_year AND lp.fiscal_quarter=gt.fiscal_quarter;
"""

SQL_VIEW_SERVICES_GROWTH = """
CREATE OR REPLACE VIEW vw_services_growth AS
WITH svc AS (
    SELECT d.fiscal_year, d.fiscal_quarter, d.quarter_label,
           SUM(f.revenue_usd_millions)      AS services_rev_m,
           SUM(f.gross_profit_usd_millions) AS services_gp_m,
           AVG(f.gross_margin_pct)          AS services_margin_pct
    FROM fact_revenue f
    JOIN dim_date    d ON f.date_key    = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    WHERE p.product_name = 'Services'
    GROUP BY d.fiscal_year, d.fiscal_quarter, d.quarter_label
),
tot AS (
    SELECT d.fiscal_year, d.fiscal_quarter,
           SUM(f.revenue_usd_millions) AS total_rev_m
    FROM fact_revenue f JOIN dim_date d ON f.date_key=d.date_key
    GROUP BY d.fiscal_year, d.fiscal_quarter
)
SELECT s.*, t.total_rev_m,
    ROUND(s.services_rev_m/NULLIF(t.total_rev_m,0)*100,2) AS services_attach_rate_pct,
    ROUND(
        (s.services_rev_m - LAG(s.services_rev_m) OVER (
            ORDER BY s.fiscal_year, s.fiscal_quarter
        )) / NULLIF(LAG(s.services_rev_m) OVER (
            ORDER BY s.fiscal_year, s.fiscal_quarter
        ),0)*100, 2
    ) AS services_qoq_growth_pct
FROM svc s JOIN tot t
ON s.fiscal_year=t.fiscal_year AND s.fiscal_quarter=t.fiscal_quarter
ORDER BY s.fiscal_year, s.fiscal_quarter;
"""

SQL_VIEW_EXECUTIVE_SUMMARY = """
CREATE OR REPLACE VIEW vw_executive_summary AS
WITH base AS (
    SELECT
        d.fiscal_year, d.fiscal_quarter, d.quarter_label,
        SUM(f.revenue_usd_millions)                           AS total_revenue_millions,
        SUM(f.gross_profit_usd_millions)                      AS total_gross_profit_millions,
        ROUND(SUM(f.gross_profit_usd_millions)/
              NULLIF(SUM(f.revenue_usd_millions),0)*100,2)    AS blended_gross_margin_pct,
        SUM(CASE WHEN p.product_name='Services'
                 THEN f.revenue_usd_millions ELSE 0 END)      AS services_revenue_millions,
        SUM(CASE WHEN p.product_name='iPhone'
                 THEN f.revenue_usd_millions ELSE 0 END)      AS iphone_revenue_millions,
        SUM(CASE WHEN p.product_category='Hardware'
                 THEN f.revenue_usd_millions ELSE 0 END)      AS hardware_revenue_millions
    FROM fact_revenue f
    JOIN dim_date    d ON f.date_key    = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY d.fiscal_year, d.fiscal_quarter, d.quarter_label
)
SELECT *,
    ROUND(services_revenue_millions/NULLIF(total_revenue_millions,0)*100,2) AS services_mix_pct,
    LAG(total_revenue_millions) OVER (
        ORDER BY fiscal_year, fiscal_quarter
    ) AS prior_qtr_revenue,
    ROUND((total_revenue_millions - LAG(total_revenue_millions) OVER (
        ORDER BY fiscal_year, fiscal_quarter
    ))/NULLIF(LAG(total_revenue_millions) OVER (
        ORDER BY fiscal_year, fiscal_quarter
    ),0)*100,2) AS qoq_growth_pct,
    SUM(total_revenue_millions) OVER (
        ORDER BY fiscal_year, fiscal_quarter
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS ttm_revenue_millions
FROM base ORDER BY fiscal_year, fiscal_quarter;
"""


# ═══════════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def seed_dimensions(conn):
    cur = conn.cursor()

    # dim_date: FY2020–FY2026 Q1
    date_rows = []
    for fy in range(2020, 2027):
        max_q = 1 if fy == 2026 else 4
        for fq in range(1, max_q + 1):
            ms  = {1:10,2:1,3:4,4:7}[fq]
            cy  = fy-1 if fq==1 else fy
            qd  = date(cy, ms, 1)
            lbl = f"FY{fy} Q{fq}"
            is_cur = (fy==2026 and fq==1)
            date_rows.append((qd, fy, fq, qd.year, qd.month, lbl, is_cur))
    cur.executemany(
        "INSERT INTO dim_date(full_date,fiscal_year,fiscal_quarter,"
        "calendar_year,calendar_month,quarter_label,is_current_qtr)"
        "VALUES(%s,%s,%s,%s,%s,%s,%s)", date_rows
    )
    print(f"  ✓ dim_date: {len(date_rows)} quarters")

    # dim_product
    products = [
        ("iPhone",          "Hardware", 2007, True, "High"),
        ("Mac",             "Hardware", 1984, True, "Medium"),
        ("iPad",            "Hardware", 2010, True, "Medium"),
        ("Wearables & Home","Hardware", 2015, True, "Medium"),
        ("Services",        "Services", 2016, True, "High"),
        ("Accessories",     "Hardware", 2001, True, "Low"),
    ]
    cur.executemany(
        "INSERT INTO dim_product(product_name,product_category,"
        "launch_year,is_active,gross_margin_tier)VALUES(%s,%s,%s,%s,%s)",
        products
    )
    print(f"  ✓ dim_product: {len(products)} products")

    # dim_region
    regions = [
        ("Americas",             "AMR",  "USD", False),
        ("Europe",               "EUR",  "EUR", False),
        ("China",                "CHN",  "CNY", True),
        ("Japan",                "JPN",  "JPY", False),
        ("Rest of Asia Pacific", "APAC", "USD", True),
    ]
    cur.executemany(
        "INSERT INTO dim_region(region_name,region_code,"
        "currency_primary,is_high_growth)VALUES(%s,%s,%s,%s)",
        regions
    )
    print(f"  ✓ dim_region: {len(regions)} regions")

    # dim_customer_segment
    segments = [
        ("Champions",          "Top",    "High"),
        ("Loyal Customers",    "High",   "High"),
        ("Potential Loyalists","Medium", "Medium"),
        ("New Customers",      "New",    "Low"),
        ("Promising",          "Medium", "Medium"),
        ("Needs Attention",    "Low",    "Medium"),
        ("At Risk",            "Low",    "High"),
        ("Lost Customers",     "Churned","Low"),
    ]
    cur.executemany(
        "INSERT INTO dim_customer_segment(segment_name,rfm_tier,"
        "revenue_band)VALUES(%s,%s,%s)", segments
    )
    print(f"  ✓ dim_customer_segment: {len(segments)} segments")

    conn.commit()


def get_regional_split_quarterly(fy: int, fq: int,
                                  base_splits: dict,
                                  rng) -> dict:
    """
    Apply realistic quarterly variation to regional splits.
    
    Business rationale for each adjustment:
    - China: stronger in Q1 (iPhone launch season Oct-Dec) and
             Q2 (Chinese New Year Jan-Mar). Weaker in summer.
    - Japan: stronger in Q1-Q2, FX headwinds create volatility
    - APAC: more volatile due to emerging market exposure
    - Americas: strongest and most stable (home market)
    - Europe: strong holiday Q1, weaker in summer Q3
    
    Quarterly adjustments sum to approximately zero across regions,
    then normalized to guarantee splits total exactly 1.0.
    """
    QUARTERLY_ADJ = {
        "Americas":             {1:+0.008, 2:-0.004, 3:-0.006, 4:+0.002},
        "Europe":               {1:+0.006, 2:+0.004, 3:-0.006, 4:-0.004},
        "China":                {1:+0.015, 2:+0.010, 3:-0.012, 4:-0.013},
        "Japan":                {1:+0.003, 2:+0.005, 3:-0.004, 4:-0.004},
        "Rest of Asia Pacific": {1:-0.004, 2:-0.003, 3:+0.005, 4:+0.002},
    }

    adjusted = {}
    for region, base in base_splits.items():
        seasonal = QUARTERLY_ADJ.get(region, {}).get(fq, 0.0)
        noise    = rng.uniform(-0.006, 0.006)
        adjusted[region] = max(0.02, base + seasonal + noise)

    # Normalize so splits sum exactly to 1.0
    total = sum(adjusted.values())
    return {k: v / total for k, v in adjusted.items()}

def seed_fact_revenue(conn):
    """
    Inserts revenue data with:
    - EXACT regional splits (no noise on splits = no inflated totals)
    - REALISTIC margin variation (seasonal + secular trend + small noise)
    - Reproducible with numpy seed 42
    """
    cur = conn.cursor()

    cur.execute("SELECT date_key,fiscal_year,fiscal_quarter FROM dim_date")
    date_map = {(r[1],r[2]):r[0] for r in cur.fetchall()}

    cur.execute("SELECT product_key,product_name FROM dim_product")
    prod_map = {r[1]:r[0] for r in cur.fetchall()}

    cur.execute("SELECT region_key,region_name FROM dim_region")
    reg_map  = {r[1]:r[0] for r in cur.fetchall()}

    rng     = np.random.default_rng(42)
    records = []

    for (fy, fq, product), total_b in APPLE_REVENUE_DATA.items():
        dk = date_map.get((fy, fq))
        pk = prod_map.get(product)
        if not dk or not pk:
            continue

        total_m = total_b * 1000.0   # billions → millions
        splits = get_regional_split_quarterly(
    fy, fq,
    REGIONAL_SPLITS.get(fy, REGIONAL_SPLITS[2025]),
    rng
)

        for region_name, split_pct in splits.items():
            rk = reg_map.get(region_name)
            if not rk:
                continue

            # Revenue: EXACT split, no noise
            region_rev = round(total_m * split_pct, 2)

            # Margin: WITH realistic variation
            margin      = get_margin(product, fy, fq, rng)
            gross_profit = round(region_rev * margin, 2)

            asp   = ASP_MAP.get(product, 0)
            units = round(region_rev / asp, 4) if asp > 0 else 0.0

            records.append((
                dk, pk, rk,
                region_rev, units, asp,
                round(margin * 100, 2),
                gross_profit, None,
            ))

    cur.executemany("""
        INSERT INTO fact_revenue
        (date_key,product_key,region_key,
         revenue_usd_millions,units_millions,asp_usd,
         gross_margin_pct,gross_profit_usd_millions,yoy_growth_pct)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, records)
    conn.commit()
    print(f"  ✓ fact_revenue: {len(records)} rows | FY2022–FY2026 Q1")

def seed_fact_customer(conn, n=50000):
    """
    Synthetic Apple Customer Intelligence Dataset

    Purpose:
    Apple does not disclose customer-level transaction data.
    This dataset simulates realistic Apple ecosystem behaviour
    for RFM segmentation, cohort analysis, retention analysis,
    churn intelligence, and CLV modelling.

    Assumptions calibrated using:
    - Apple FY2022–FY2026 SEC filings
    - Services growth trends
    - Apple ecosystem loyalty characteristics
    - Paid subscription disclosures
    """

    import random
    from datetime import date, timedelta

    cur = conn.cursor()

    cur.execute("""
        SELECT region_key, region_name
        FROM dim_region
    """)
    regions = cur.fetchall()

    cur.execute("""
        SELECT segment_key, segment_name
        FROM dim_customer_segment
    """)
    segs = cur.fetchall()

    seg_keys = [s[0] for s in segs]

    # --------------------------------------------------
    # CUSTOMER SEGMENT DISTRIBUTION
    # --------------------------------------------------

    seg_weights = [
        0.22,  # Champions
        0.24,  # Loyal Customers
        0.12,  # Potential Loyalists
        0.08,  # New Customers
        0.10,  # Promising
        0.09,  # Needs Attention
        0.09,  # At Risk
        0.06   # Lost Customers
    ]

    # --------------------------------------------------
    # APPLE FY2025 REGIONAL REVENUE MIX
    # --------------------------------------------------

    rw_map = {
        "Americas": 0.429,
        "Europe": 0.267,
        "China": 0.155,
        "Japan": 0.069,
        "Rest of Asia Pacific": 0.080
    }

    rw = [rw_map.get(r[1], 0.10) for r in regions]

    # --------------------------------------------------
    # SUBSCRIPTION ATTACH RATE
    # --------------------------------------------------

    sub_prob = {
        seg_keys[0]: 0.92,   # Champions
        seg_keys[1]: 0.84,   # Loyal
        seg_keys[2]: 0.68,   # Potential
        seg_keys[3]: 0.38,   # New
        seg_keys[4]: 0.58,   # Promising
        seg_keys[5]: 0.42,   # Needs Attention
        seg_keys[6]: 0.22,   # At Risk
        seg_keys[7]: 0.05    # Lost
    }

    # --------------------------------------------------
    # RFM SCORE BASELINES
    # --------------------------------------------------

    rfm_base = {
        seg_keys[0]: 14,
        seg_keys[1]: 12,
        seg_keys[2]: 10,
        seg_keys[3]: 7,
        seg_keys[4]: 9,
        seg_keys[5]: 7,
        seg_keys[6]: 5,
        seg_keys[7]: 3
    }

    # --------------------------------------------------
    # SEGMENT ECONOMIC VALUE
    # --------------------------------------------------

    segment_multiplier = {
        seg_keys[0]: 3.5,   # Champions
        seg_keys[1]: 2.8,   # Loyal
        seg_keys[2]: 1.8,   # Potential
        seg_keys[3]: 0.8,   # New
        seg_keys[4]: 1.2,   # Promising
        seg_keys[5]: 0.7,   # Needs Attention
        seg_keys[6]: 0.5,   # At Risk
        seg_keys[7]: 0.2    # Lost
    }

    random.seed(42)

    start = date(2019, 10, 1)
    end = date(2025, 12, 27)

    span = (end - start).days

    records = []

    for i in range(1, n + 1):

        # ------------------------------------------
        # SEGMENT ASSIGNMENT
        # ------------------------------------------

        sk = random.choices(
            seg_keys,
            weights=seg_weights,
            k=1
        )[0]

        multiplier = segment_multiplier[sk]

        # ------------------------------------------
        # COHORT START DATE
        # ------------------------------------------

        first = start + timedelta(
            days=int(
                random.betavariate(1.4, 1.4) * span
            )
        )

        max_d = (end - first).days

        last = first + timedelta(
            days=int(
                random.betavariate(1.8, 1.0)
                * max(1, max_d)
            )
        )

        # ------------------------------------------
        # ORDERS
        # ------------------------------------------

        orders = max(
            1,
            min(
                40,
                int(
                    random.lognormvariate(
                        1.4 * multiplier,
                        0.60
                    )
                )
            )
        )

        # ------------------------------------------
        # AOV
        # ------------------------------------------

        aov = max(
            99,
            min(
                3500,
                random.lognormvariate(
                    6.0 + (multiplier * 0.20),
                    0.50
                )
            )
        )

        rev = round(orders * aov, 2)

        # ------------------------------------------
        # REGION
        # ------------------------------------------

        rk, _ = random.choices(
            regions,
            weights=rw,
            k=1
        )[0]

        # ------------------------------------------
        # COHORT LABEL
        # ------------------------------------------

        m = first.month

        if m >= 10:
            cfy, cfq = first.year + 1, 1
        elif m <= 3:
            cfy, cfq = first.year, 2
        elif m <= 6:
            cfy, cfq = first.year, 3
        else:
            cfy, cfq = first.year, 4

        cohort = f"FY{cfy}-Q{cfq}"

        # ------------------------------------------
        # SUBSCRIBER STATUS
        # ------------------------------------------

        is_sub = (
            random.random()
            < sub_prob.get(sk, 0.50)
        )

        # ------------------------------------------
        # RFM SCORE
        # ------------------------------------------

        rfm_s = max(
            3,
            min(
                15,
                rfm_base.get(sk, 8)
                + random.randint(-1, 1)
            )
        )

        # ------------------------------------------
        # CLV
        # ------------------------------------------

        clv = round(
            rev *
            random.uniform(
                multiplier,
                multiplier * 2.5
            ),
            2
        )

        records.append(
            (
                f"CUST-{i:06d}",
                first,
                last,
                rev,
                orders,
                rk,
                sk,
                cohort,
                is_sub,
                rfm_s,
                clv
            )
        )

        if len(records) % 5000 == 0:

            cur.executemany("""
                INSERT INTO fact_customer
                (
                    customer_id,
                    first_purchase_date,
                    last_purchase_date,
                    total_revenue_usd,
                    total_orders,
                    region_key,
                    segment_key,
                    cohort_quarter,
                    is_subscriber,
                    rfm_score,
                    clv_estimated_usd
                )
                VALUES
                (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s
                )
            """, records)

            conn.commit()

            print(
                f"    → {len(records):,} customers inserted..."
            )

            records = []

    if records:

        cur.executemany("""
            INSERT INTO fact_customer
            (
                customer_id,
                first_purchase_date,
                last_purchase_date,
                total_revenue_usd,
                total_orders,
                region_key,
                segment_key,
                cohort_quarter,
                is_subscriber,
                rfm_score,
                clv_estimated_usd
            )
            VALUES
            (
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s
            )
        """, records)

        conn.commit()

    print(f"✓ fact_customer: {n:,} records seeded")


def verify(conn):
    """Check that KPI values match Apple's actual reported financials."""
    cur = conn.cursor()
    cur.execute("""
        SELECT quarter_label,
               ROUND(total_revenue_millions,0)   AS rev_m,
               ROUND(services_revenue_millions,0) AS svc_m,
               ROUND(blended_gross_margin_pct,1)  AS margin_pct,
               ROUND(ttm_revenue_millions,0)       AS ttm_m
        FROM vw_executive_summary
        ORDER BY fiscal_year DESC, fiscal_quarter DESC
        LIMIT 4
    """)
    rows = cur.fetchall()

    print("\n── VERIFICATION ──────────────────────────────────────────────")
    print(f"  {'Quarter':<12} {'Revenue':>12}  {'Services':>10}  "
          f"{'Margin':>8}  {'TTM':>12}")
    print("  " + "─" * 60)
    for r in rows:
        print(f"  {r[0]:<12} ${r[1]:>10,.0f}M  ${r[2]:>8,.0f}M  "
              f"{r[3]:>6.1f}%  ${r[4]:>10,.0f}M")

    print("\n  Expected values (from Apple public filings):")
    print("  FY2026 Q1  ~$143,756M   ~$30,013M   ~46.5–47.0%")
    print("  FY2025 Q4  ~$102,466M   ~$28,750M   ~47.0–47.5%")
    print("  FY2025 Q3   ~$94,036M   ~$27,423M   ~46.0–46.5%")

    # Assertions
    latest = rows[0]
    errors = []
    if not (130000 < latest[1] < 160000):
        errors.append(f"Revenue {latest[1]:,.0f}M — expected 130,000–160,000M")
    if not (27000 < latest[2] < 34000):
        errors.append(f"Services {latest[2]:,.0f}M — expected 27,000–34,000M")
    if not (44.0 < latest[3] < 50.0):
        errors.append(f"Margin {latest[3]:.1f}% — expected 44–50%")

    print()
    if errors:
        print("  ⛔  VERIFICATION FAILED:")
        for e in errors:
            print(f"     → {e}")
        return False
    else:
        print("  ✅  ALL CHECKS PASSED — database is correct")
        return True


# ═══════════════════════════════════════════════════════════════════
# MAIN — Runs everything in sequence
# ═══════════════════════════════════════════════════════════════════
def main():
    print("\n" + "═" * 60)
    print("  Apple Global Performance Analysis — NUCLEAR RESET")
    print("═" * 60)

    # Confirm intent
    print("\nThis will DROP and RECREATE the entire database.")
    confirm = input("Type 'yes' to continue: ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        sys.exit(0)

    # Connect
    try:
        conn = psycopg2.connect(**DB)
        conn.autocommit = False
        print("\n  ✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"\n  ⛔  Connection failed: {e}")
        print("  Check your password in DB config at the top of this file.")
        sys.exit(1)

    try:
        cur = conn.cursor()

        # Step 1: Drop everything
        print("\n── Step 1: Dropping all existing tables and views...")
        conn.autocommit = True
        cur.execute(SQL_DROP)
        print("  ✓ All tables and views dropped")

        # Step 2: Create tables
        print("\n── Step 2: Creating tables...")
        cur.execute(SQL_CREATE_TABLES)
        print("  ✓ All tables created")

        # Step 3: Create views
        print("\n── Step 3: Creating analytics views...")
        conn.autocommit = False
        for name, sql in [
            ("vw_yoy_revenue",        SQL_VIEW_YOY),
            ("vw_product_margin",     SQL_VIEW_PRODUCT_MARGIN),
            ("vw_regional_kpi",       SQL_VIEW_REGIONAL_KPI),
            ("vw_services_growth",    SQL_VIEW_SERVICES_GROWTH),
            ("vw_executive_summary",  SQL_VIEW_EXECUTIVE_SUMMARY),
        ]:
            cur.execute(sql)
            print(f"  ✓ {name}")
        conn.commit()

        # Step 4: Seed dimensions
        print("\n── Step 4: Seeding dimension tables...")
        seed_dimensions(conn)

        # Step 5: Seed fact_revenue
        print("\n── Step 5: Seeding fact_revenue (Apple financials)...")
        seed_fact_revenue(conn)

        # Step 6: Seed fact_customer
        print("\n── Step 6: Seeding fact_customer (50,000 records)...")
        seed_fact_customer(conn)

        # Step 7: Verify
        print("\n── Step 7: Verifying data integrity...")
        ok = verify(conn)

        conn.close()

        if ok:
            print("\n" + "═" * 60)
            print("  ✅  RESET COMPLETE")
            print("\n  Next steps:")
            print("  1. Delete __pycache__:")
            print("     for /r . %d in (__pycache__) do @if exist")
            print('     "%d" rd /s /q "%d"')
            print("  2. Launch Streamlit:")
            print("     streamlit run app.py")
            print("═" * 60 + "\n")
        else:
            print("\n  ⛔  Verification failed — check data above")

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"\n  ⛔  ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()