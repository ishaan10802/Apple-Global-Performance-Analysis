# Data Dictionary — Apple Global Performance Analysis Platform

**Database:** `apple_intelligence` (PostgreSQL)
**Coverage:** FY2022 Q1 — FY2026 Q1 (17 fiscal quarters)
**Customer records:** 50,000 records (FY2019–FY2025)

---

## Dimension Tables

### `dim_date`
Calendar and fiscal date spine. Every financial record joins here.

| Column | Type | Description |
|---|---|---|
| date_key | SERIAL PK | Surrogate key |
| full_date | DATE | First day of the fiscal quarter |
| fiscal_year | INT | Apple fiscal year (Oct–Sep) |
| fiscal_quarter | INT | 1=Oct–Dec, 2=Jan–Mar, 3=Apr–Jun, 4=Jul–Sep |
| calendar_year | INT | Calendar year of quarter start |
| calendar_month | INT | Calendar month of quarter start |
| quarter_label | VARCHAR | Display label e.g. "FY2025 Q1" |
| is_current_qtr | BOOLEAN | TRUE for the most recent loaded quarter |

### `dim_product`
Apple's six product lines.

| Column | Type | Description |
|---|---|---|
| product_key | SERIAL PK | Surrogate key |
| product_name | VARCHAR | iPhone / Mac / iPad / Wearables & Home / Services / Accessories |
| product_category | VARCHAR | "Hardware" or "Services" |
| launch_year | INT | Year product line was introduced |
| gross_margin_tier | VARCHAR | High / Medium / Low margin classification |

### `dim_region`
Apple's five official geographic reporting segments.

| Column | Type | Description |
|---|---|---|
| region_key | SERIAL PK | Surrogate key |
| region_name | VARCHAR | Americas / Europe / China / Japan / Rest of Asia Pacific |
| region_code | VARCHAR | AMR / EUR / CHN / JPN / APAC |
| is_high_growth | BOOLEAN | TRUE for strategically high-growth markets |

### `dim_customer_segment`
Eight RFM-based customer segments.

| Segment | Description |
|---|---|
| Champions | High R, F, M — most valuable, recently active |
| Loyal Customers | Consistently purchasing, high value |
| Potential Loyalists | Recent buyers with growth potential |
| New Customers | Very recent first purchase |
| Promising | Above average but not yet loyal |
| Needs Attention | Slipping engagement |
| At Risk | Once valuable, now inactive |
| Lost Customers | Not purchased in 365+ days |

---

## Fact Tables

### `fact_revenue`
**Core financial fact table.** One row = one product × one region × one quarter.
Powers 80% of all platform analytics.

| Column | Type | Description |
|---|---|---|
| revenue_key | SERIAL PK | Surrogate key |
| date_key | INT FK | Links to dim_date |
| product_key | INT FK | Links to dim_product |
| region_key | INT FK | Links to dim_region |
| revenue_usd_millions | DECIMAL | Revenue in USD millions |
| units_millions | DECIMAL | Units sold in millions (0 for Services) |
| asp_usd | DECIMAL | Average Selling Price in USD |
| gross_margin_pct | DECIMAL | Gross margin as % of revenue |
| gross_profit_usd_millions | DECIMAL | Revenue × gross_margin_pct |
| yoy_growth_pct | DECIMAL | % change vs same quarter prior year |

### `fact_customer`
**50,000 synthetic Apple customers.** Powers RFM, cohort, and churn analytics.

| Column | Type | Description |
|---|---|---|
| customer_id | VARCHAR | "CUST-000001" to "CUST-050000" |
| first_purchase_date | DATE | Defines the customer's cohort |
| last_purchase_date | DATE | Used for recency and churn detection |
| total_revenue_usd | DECIMAL | Lifetime spend across all products |
| total_orders | INT | Total number of purchase events |
| region_key | INT FK | Geographic region |
| segment_key | INT FK | RFM segment assignment |
| cohort_quarter | VARCHAR | e.g. "FY2022-Q1" |
| is_subscriber | BOOLEAN | TRUE if Apple Services subscriber (~55%) |
| rfm_score | INT | Composite RFM score (3–15) |
| clv_estimated_usd | DECIMAL | Estimated Customer Lifetime Value |

---

## Analytics Views

### `vw_executive_summary`
One row per fiscal quarter with all top-line KPIs.
**Primary view for executive dashboard.**

Key columns: `total_revenue_millions`, `blended_gross_margin_pct`,
`services_mix_pct`, `qoq_growth_pct`, `ttm_revenue_millions`

### `vw_product_margin`
Revenue and margin by product × quarter.
Includes `revenue_mix_pct` and `ytd_revenue_millions`.

### `vw_regional_kpi`
Revenue by geography with share %, QoQ growth, and risk flags.

### `vw_services_growth`
Services-specific metrics including `services_attach_rate_pct`
and `services_qoq_growth_pct`.

### `vw_yoy_revenue`
Year-over-year growth calculations using LAG window functions.
Includes `yoy_growth_pct` and `yoy_delta_m`.

---

## Business Glossary

| Term | Definition |
|---|---|
| ASP | Average Selling Price = Revenue ÷ Units sold |
| Attach Rate | Services revenue as % of total company revenue |
| TTM | Trailing Twelve Months = rolling 4-quarter sum |
| YoY | Year-over-Year = % change vs same quarter last year |
| QoQ | Quarter-over-Quarter = % change vs immediately prior quarter |
| Blended Margin | Company-wide gross margin across all products |
| Services Premium | Margin gap between Services (~75%) and Hardware (~37%) |
| CLV | Customer Lifetime Value = estimated future revenue from one customer |
| RFM | Recency × Frequency × Monetary scoring model |
| HHI | Herfindahl-Hirschman Index = revenue concentration measure |
| FY | Apple Fiscal Year (Oct 1 – Sep 30) |

---

## Data Sources

| Source | Type | Files in data/raw/ |
|---|---|---|
| Apple 8-K Earnings Releases | Official SEC filing | apple_8k_fy2025_q*.htm |
| Apple 10-Q Quarterly Reports | Official SEC filing | apple_10q_fy2025_q*.htm |
| Apple 10-K Annual Report | Official SEC filing | apple_10k_2025.pdf |
| apple_official_quarterly_revenue.csv | Compiled reference | data/raw/ |
| Synthetic customer records | Python-generated | data/synthetic/ |

All financial figures in `fact_revenue` are sourced directly from
Apple's official SEC filings and are publicly available at
`investor.apple.com` and `sec.gov`.