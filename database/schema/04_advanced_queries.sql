-- 04_advanced_queries.sql
-- Reference queries for interviews. Run these individually to verify data.

-- 1. Services strategic pivot
SELECT quarter_label,
       ROUND(services_revenue_millions,0) AS services_m,
       ROUND(total_revenue_millions,0)    AS total_m,
       services_mix_pct,
       blended_gross_margin_pct
FROM vw_executive_summary
ORDER BY fiscal_year, fiscal_quarter;

-- 2. Revenue concentration (Herfindahl Index)
WITH shares AS (
    SELECT fiscal_year, fiscal_quarter, quarter_label,
           product_name, revenue_mix_pct/100.0 AS share
    FROM vw_product_margin
)
SELECT fiscal_year, quarter_label,
       ROUND(SUM(share*share),4) AS hhi,
       CASE WHEN SUM(share*share)>0.25 THEN 'High concentration'
            WHEN SUM(share*share)>0.15 THEN 'Moderate'
            ELSE 'Diversified' END AS risk_level
FROM shares GROUP BY fiscal_year, fiscal_quarter, quarter_label
ORDER BY fiscal_year, fiscal_quarter;

-- 3. China revenue risk monitor
SELECT quarter_label, revenue_usd_millions AS china_rev_m,
       region_share_pct, qoq_growth_pct
FROM vw_regional_kpi
WHERE region_name='China'
ORDER BY fiscal_year, fiscal_quarter;

-- 4. TTM revenue by product
SELECT product_name, quarter_label,
       ROUND(SUM(revenue_usd_millions) OVER (
           PARTITION BY product_name
           ORDER BY fiscal_year, fiscal_quarter
           ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
       ),0) AS ttm_rev_m
FROM vw_product_margin
ORDER BY product_name, fiscal_year, fiscal_quarter;

-- 5. Services margin premium vs hardware
SELECT quarter_label,
       ROUND(AVG(CASE WHEN product_category='Services'
                      THEN gross_margin_pct END),1) AS services_margin,
       ROUND(AVG(CASE WHEN product_category='Hardware'
                      THEN gross_margin_pct END),1) AS hardware_margin,
       ROUND(AVG(CASE WHEN product_category='Services'
                      THEN gross_margin_pct END) -
             AVG(CASE WHEN product_category='Hardware'
                      THEN gross_margin_pct END),1) AS premium_pp
FROM vw_product_margin
GROUP BY fiscal_year, fiscal_quarter, quarter_label
ORDER BY fiscal_year, fiscal_quarter;