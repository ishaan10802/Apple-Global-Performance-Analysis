-- 02_create_facts.sql

CREATE TABLE IF NOT EXISTS fact_revenue (
    revenue_key               SERIAL PRIMARY KEY,
    date_key                  INT REFERENCES dim_date(date_key),
    product_key               INT REFERENCES dim_product(product_key),
    region_key                INT REFERENCES dim_region(region_key),
    revenue_usd_millions      DECIMAL(12,2) NOT NULL,
    units_millions            DECIMAL(10,4),
    asp_usd                   DECIMAL(10,2),
    gross_margin_pct          DECIMAL(6,2),
    gross_profit_usd_millions DECIMAL(12,2),
    yoy_growth_pct            DECIMAL(8,2)
);

CREATE TABLE IF NOT EXISTS fact_subscriptions (
    subscription_key               SERIAL PRIMARY KEY,
    date_key                       INT REFERENCES dim_date(date_key),
    region_key                     INT REFERENCES dim_region(region_key),
    paid_subscriptions_millions    DECIMAL(8,2),
    services_revenue_usd_millions  DECIMAL(12,2),
    subscriber_growth_pct          DECIMAL(6,2),
    arpu_usd                       DECIMAL(8,2)
);

CREATE TABLE IF NOT EXISTS fact_customer (
    customer_key          SERIAL PRIMARY KEY,
    customer_id           VARCHAR(20) UNIQUE,
    first_purchase_date   DATE,
    last_purchase_date    DATE,
    total_revenue_usd     DECIMAL(12,2),
    total_orders          INT,
    region_key            INT REFERENCES dim_region(region_key),
    segment_key           INT REFERENCES dim_customer_segment(segment_key),
    cohort_quarter        VARCHAR(12),
    is_subscriber         BOOLEAN DEFAULT FALSE,
    rfm_score             INT,
    clv_estimated_usd     DECIMAL(12,2)
);