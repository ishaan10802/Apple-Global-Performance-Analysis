-- 03_create_views.sql

-- ── VIEW 1: YoY Revenue Growth ────────────────────────────────────
CREATE OR REPLACE VIEW vw_yoy_revenue AS
WITH base AS (
    SELECT
        d.fiscal_year, d.fiscal_quarter, d.quarter_label,
        p.product_name, p.product_category,
        r.region_name,
        SUM(f.revenue_usd_millions)      AS revenue_usd_millions,
        SUM(f.gross_profit_usd_millions) AS gross_profit_usd_millions,
        AVG(f.gross_margin_pct)          AS avg_gross_margin_pct,
        SUM(f.units_millions)            AS units_millions
    FROM fact_revenue f
    JOIN dim_date    d ON f.date_key    = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_region  r ON f.region_key  = r.region_key
    GROUP BY d.fiscal_year,d.fiscal_quarter,d.quarter_label,
             p.product_name,p.product_category,r.region_name
),

lagged AS (
    SELECT *,
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

-- ── VIEW 2: Product Margin ────────────────────────────────────────
CREATE OR REPLACE VIEW vw_product_margin AS
SELECT
    d.fiscal_year, d.fiscal_quarter, d.quarter_label,
    p.product_name, p.product_category, p.gross_margin_tier,
    SUM(f.revenue_usd_millions)                 AS revenue_usd_millions,
    SUM(f.gross_profit_usd_millions)            AS gross_profit_usd_millions,
    ROUND(AVG(f.gross_margin_pct),2)            AS gross_margin_pct,
    SUM(f.units_millions)                       AS units_millions,
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
GROUP BY d.fiscal_year,d.fiscal_quarter,d.quarter_label,
         p.product_name,p.product_category,p.gross_margin_tier;

-- ── VIEW 3: Regional KPI ──────────────────────────────────────────
CREATE OR REPLACE VIEW vw_regional_kpi AS
WITH rt AS (
    SELECT
        d.fiscal_year, d.fiscal_quarter, d.quarter_label,
        r.region_name, r.region_code, r.is_high_growth,
        SUM(f.revenue_usd_millions)      AS revenue_usd_millions,
        SUM(f.gross_profit_usd_millions) AS gross_profit_usd_millions,
        ROUND(AVG(f.gross_margin_pct),2) AS avg_margin_pct
    FROM fact_revenue f
    JOIN dim_date   d ON f.date_key   = d.date_key
    JOIN dim_region r ON f.region_key = r.region_key
    GROUP BY d.fiscal_year,d.fiscal_quarter,d.quarter_label,
             r.region_name,r.region_code,r.is_high_growth
),
gt AS (
    SELECT fiscal_year, fiscal_quarter,
           SUM(revenue_usd_millions) AS global_rev_m
    FROM rt GROUP BY fiscal_year, fiscal_quarter
),
lp AS (
    SELECT *,
        LAG(revenue_usd_millions) OVER (
            PARTITION BY region_name
            ORDER BY fiscal_year, fiscal_quarter
        ) AS prior_rev
    FROM rt
)
SELECT
    lp.*, gt.global_rev_m,
    ROUND(lp.revenue_usd_millions/NULLIF(gt.global_rev_m,0)*100,2) AS region_share_pct,
    CASE WHEN lp.prior_rev > 0
         THEN ROUND(((lp.revenue_usd_millions-lp.prior_rev)/lp.prior_rev)*100,2)
         ELSE NULL END AS qoq_growth_pct
FROM lp
JOIN gt ON lp.fiscal_year=gt.fiscal_year
       AND lp.fiscal_quarter=gt.fiscal_quarter;

-- ── VIEW 4: Services Growth ───────────────────────────────────────
CREATE OR REPLACE VIEW vw_services_growth AS
WITH svc AS (
    SELECT
        d.fiscal_year, d.fiscal_quarter, d.quarter_label,
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
SELECT
    s.*,
    t.total_rev_m,
    ROUND(s.services_rev_m/NULLIF(t.total_rev_m,0)*100,2) AS services_attach_rate_pct,
    ROUND((s.services_rev_m - LAG(s.services_rev_m) OVER (
        ORDER BY s.fiscal_year,s.fiscal_quarter
    ))/NULLIF(LAG(s.services_rev_m) OVER (
        ORDER BY s.fiscal_year,s.fiscal_quarter
    ),0)*100,2) AS services_qoq_growth_pct
FROM svc s JOIN tot t
  ON s.fiscal_year=t.fiscal_year AND s.fiscal_quarter=t.fiscal_quarter
ORDER BY s.fiscal_year, s.fiscal_quarter;

-- ── VIEW 5: Executive Summary ─────────────────────────────────────
CREATE OR REPLACE VIEW vw_executive_summary AS
WITH base AS (
    SELECT
        d.fiscal_year, d.fiscal_quarter, d.quarter_label,
        SUM(f.revenue_usd_millions)                              AS total_revenue_millions,
        SUM(f.gross_profit_usd_millions)                         AS total_gross_profit_millions,
        ROUND(SUM(f.gross_profit_usd_millions)/
              NULLIF(SUM(f.revenue_usd_millions),0)*100,2)       AS blended_gross_margin_pct,
        SUM(CASE WHEN p.product_name='Services'
                 THEN f.revenue_usd_millions ELSE 0 END)         AS services_revenue_millions,
        SUM(CASE WHEN p.product_name='iPhone'
                 THEN f.revenue_usd_millions ELSE 0 END)         AS iphone_revenue_millions,
        SUM(CASE WHEN p.product_category='Hardware'
                 THEN f.revenue_usd_millions ELSE 0 END)         AS hardware_revenue_millions
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