-- 01_create_dimensions.sql
-- Run this first in SQLTools (Ctrl+A then right-click → Run Selected Query)

CREATE TABLE IF NOT EXISTS dim_date (
    date_key        SERIAL PRIMARY KEY,
    full_date       DATE NOT NULL,
    fiscal_year     INT  NOT NULL,
    fiscal_quarter  INT  NOT NULL,
    calendar_year   INT  NOT NULL,
    calendar_month  INT  NOT NULL,
    quarter_label   VARCHAR(12),
    is_current_qtr  BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key       SERIAL PRIMARY KEY,
    product_name      VARCHAR(100) NOT NULL,
    product_category  VARCHAR(50),
    launch_year       INT,
    is_active         BOOLEAN DEFAULT TRUE,
    gross_margin_tier VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS dim_region (
    region_key       SERIAL PRIMARY KEY,
    region_name      VARCHAR(100) NOT NULL,
    region_code      VARCHAR(10),
    currency_primary VARCHAR(10),
    is_high_growth   BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dim_customer_segment (
    segment_key  SERIAL PRIMARY KEY,
    segment_name VARCHAR(50),
    rfm_tier     VARCHAR(20),
    revenue_band VARCHAR(20)
);