# database/seed/seed_all_tables.py
"""
Master database seed script.
Run this once to populate the entire PostgreSQL warehouse.
Covers FY2022 Q1 through FY2026 Q1 using real Apple SEC filing data.
"""
import random

import random

import pandas as pd
import numpy as np
import psycopg2
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config_new import DB_CONFIG

# ─────────────────────────────────────────────────────────────────────
# REAL APPLE REVENUE DATA — sourced from official SEC 8-K filings
# All values in USD billions
# ─────────────────────────────────────────────────────────────────────
APPLE_REVENUE_DATA = {
    # FY2022 (source: Apple 8-K filings)
    (2022,1,"iPhone"):71.628,(2022,1,"Mac"):10.852,(2022,1,"iPad"):7.248,
    (2022,1,"Wearables & Home"):14.702,(2022,1,"Services"):19.516,
    (2022,2,"iPhone"):50.570,(2022,2,"Mac"):10.435,(2022,2,"iPad"):7.646,
    (2022,2,"Wearables & Home"):8.806,(2022,2,"Services"):19.821,
    (2022,3,"iPhone"):40.665,(2022,3,"Mac"):7.382,(2022,3,"iPad"):7.224,
    (2022,3,"Wearables & Home"):8.084,(2022,3,"Services"):19.604,
    (2022,4,"iPhone"):42.627,(2022,4,"Mac"):11.508,(2022,4,"iPad"):7.174,
    (2022,4,"Wearables & Home"):9.651,(2022,4,"Services"):19.188,
    # FY2023 (source: Apple 8-K filings)
    (2023,1,"iPhone"):65.775,(2023,1,"Mac"):7.735,(2023,1,"iPad"):9.396,
    (2023,1,"Wearables & Home"):13.482,(2023,1,"Services"):20.766,
    (2023,2,"iPhone"):51.334,(2023,2,"Mac"):7.168,(2023,2,"iPad"):6.670,
    (2023,2,"Wearables & Home"):8.757,(2023,2,"Services"):20.907,
    (2023,3,"iPhone"):39.669,(2023,3,"Mac"):6.840,(2023,3,"iPad"):5.791,
    (2023,3,"Wearables & Home"):8.284,(2023,3,"Services"):21.213,
    (2023,4,"iPhone"):43.805,(2023,4,"Mac"):7.614,(2023,4,"iPad"):6.443,
    (2023,4,"Wearables & Home"):9.320,(2023,4,"Services"):22.314,
    # FY2024 (source: Apple 8-K filings)
    (2024,1,"iPhone"):69.702,(2024,1,"Mac"):7.780,(2024,1,"iPad"):7.023,
    (2024,1,"Wearables & Home"):11.953,(2024,1,"Services"):23.117,
    (2024,2,"iPhone"):45.963,(2024,2,"Mac"):7.451,(2024,2,"iPad"):5.559,
    (2024,2,"Wearables & Home"):7.913,(2024,2,"Services"):23.867,
    (2024,3,"iPhone"):39.296,(2024,3,"Mac"):7.009,(2024,3,"iPad"):7.162,
    (2024,3,"Wearables & Home"):8.097,(2024,3,"Services"):24.213,
    (2024,4,"iPhone"):46.222,(2024,4,"Mac"):7.744,(2024,4,"iPad"):6.950,
    (2024,4,"Wearables & Home"):9.042,(2024,4,"Services"):24.972,
    # FY2025 — REAL DATA from Apple SEC filings
    # Q1: 8-K Jan 2025 — $124.3B record quarter
    (2025,1,"iPhone"):69.138,(2025,1,"Mac"):8.987,(2025,1,"iPad"):8.088,
    (2025,1,"Wearables & Home"):11.747,(2025,1,"Services"):26.340,
    # Q2: 10-Q May 2025 — $95.4B, up 5% YoY
    (2025,2,"iPhone"):46.841,(2025,2,"Mac"):7.949,(2025,2,"iPad"):6.402,
    (2025,2,"Wearables & Home"):7.522,(2025,2,"Services"):26.645,
    # Q3: 8-K Jul 2025 — $94.0B, up 10% YoY, June quarter record
    (2025,3,"iPhone"):44.582,(2025,3,"Mac"):8.046,(2025,3,"iPad"):6.581,
    (2025,3,"Wearables & Home"):7.404,(2025,3,"Services"):27.423,
    # Q4: 8-K Oct 2025 — $102.5B, FY2025 total $416.2B record
    (2025,4,"iPhone"):49.025,(2025,4,"Mac"):8.726,(2025,4,"iPad"):6.952,
    (2025,4,"Wearables & Home"):9.013,(2025,4,"Services"):28.750,
    # FY2026 Q1 — 10-Q Feb 2026 — $143.8B, iPhone 17 super-cycle
    (2026,1,"iPhone"):85.269,(2026,1,"Mac"):8.386,(2026,1,"iPad"):8.595,
    (2026,1,"Wearables & Home"):11.493,(2026,1,"Services"):30.013,
}

# Product gross margins (from Apple 10-K disclosures)
# ─────────────────────────────────────────────────────────────────────
# PRODUCT MARGINS — calibrated to Apple FY2025 10-K disclosures
# Products segment: 36.8% | Services segment: 75.4%
# These produce a blended gross margin of ~46.8%, matching Apple actual.
# ─────────────────────────────────────────────────────────────────────
PRODUCT_MARGINS = {
    "iPhone":           0.390,   # Was 0.470 — that inflated blended margin to 50.6%
    "Mac":              0.380,   # M-chip transition efficiency
    "iPad":             0.340,   # Mid-range hardware
    "Wearables & Home": 0.345,   # Mix of premium Watch + lower-margin HomePod
    "Services":         0.754,   # Apple FY2025 actual: 75.4%
    "Accessories":      0.350,
}

# ─────────────────────────────────────────────────────────────────────
# REGIONAL SPLITS — actual Apple geographic disclosures
# ─────────────────────────────────────────────────────────────────────
REGIONAL_SPLITS_BY_YEAR = {
    2022: {"Americas":0.440,"Europe":0.240,"China":0.190,
           "Japan":0.070,"Rest of Asia Pacific":0.060},
    2023: {"Americas":0.440,"Europe":0.250,"China":0.185,
           "Japan":0.070,"Rest of Asia Pacific":0.055},
    2024: {"Americas":0.427,"Europe":0.259,"China":0.171,
           "Japan":0.064,"Rest of Asia Pacific":0.079},
    2025: {"Americas":0.429,"Europe":0.267,"China":0.155,
           "Japan":0.069,"Rest of Asia Pacific":0.080},
    2026: {"Americas":0.430,"Europe":0.265,"China":0.150,
           "Japan":0.064,"Rest of Asia Pacific":0.091},
}

# ═════════════════════════════════════════════════════════════════════
# CUSTOMER ANALYTICS SIMULATION CONSTANTS
# ═════════════════════════════════════════════════════════════════════

# Reference date for RFM computation
# This is the "today" of our synthetic dataset.
REFERENCE_DATE  = date(2025, 12, 27)
PLATFORM_START  = date(2019, 10,  1)   # earliest possible first purchase

# ─────────────────────────────────────────────────────────────────────
# APPLE CUSTOMER PERSONAS
# Each persona models a realistic Apple buyer archetype.
# Behavioral parameters drive the simulation; no segment percentages
# are hard-coded — the distribution emerges from the simulation.
#
# Parameter guide:
#   weight              — share of the 50,000-customer population
#   tenure_years        — how long they have been a customer (min, max)
#   orders_per_year     — purchase frequency while active (min, max)
#   aov_mu / aov_sigma  — log-normal params for average order value (ln $)
#   churn_rate          — probability they have already churned
#   active_recency_days — days since last purchase if still active
#   inactive_recency_days — days since last purchase if churned
# ─────────────────────────────────────────────────────────────────────
PERSONAS = {

    # Buys every iPhone generation, multiple Apple products, all services.
    # The "Tim Cook superfan."
    'Power User': {
        'weight':                0.10,
        'tenure_years':          (3.0, 6.0),
        'orders_per_year':       (4.5, 8.0),
        'aov_mu':                7.25,    # ln($) ≈ $1,408 average order
        'aov_sigma':             0.40,
        'churn_rate':            0.04,
        'active_recency_days':   (5,   60),
        'inactive_recency_days': (400, 1100),
    },

    # Buys iPhone every 2–3 years, maybe one other device, some services.
    'Loyal Upgrader': {
        'weight':                0.19,
        'tenure_years':          (2.0, 6.0),
        'orders_per_year':       (1.8, 3.5),
        'aov_mu':                6.85,    # ln($) ≈ $943 average order
        'aov_sigma':             0.48,
        'churn_rate':            0.09,
        'active_recency_days':   (10,  150),
        'inactive_recency_days': (300, 1000),
    },

    # Manages Apple IDs for household, buys multiple devices per order.
    # High monetary value, moderate frequency.
    'Family Account': {
        'weight':                0.12,
        'tenure_years':          (2.0, 6.0),
        'orders_per_year':       (2.5, 5.0),
        'aov_mu':                7.45,    # ln($) ≈ $1,713 average order (multi-device)
        'aov_sigma':             0.50,
        'churn_rate':            0.06,
        'active_recency_days':   (10,  150),
        'inactive_recency_days': (350, 1000),
    },

    # MacBook or iPad buyer, student discount, semester-aligned purchases.
    # High churn after graduation.
    'Student': {
        'weight':                0.11,
        'tenure_years':          (0.5, 3.5),
        'orders_per_year':       (1.2, 2.5),
        'aov_mu':                6.35,    # ln($) ≈ $574 average order
        'aov_sigma':             0.48,
        'churn_rate':            0.30,
        'active_recency_days':   (30,  300),
        'inactive_recency_days': (200,  900),
    },

    # iPhone-only, long upgrade cycle, minimal ecosystem engagement.
    # Highest churn rate of any active persona.
    'Casual': {
        'weight':                0.22,
        'tenure_years':          (1.0, 6.0),
        'orders_per_year':       (0.5, 1.2),   # sub-annual purchase rate
        'aov_mu':                6.40,    # ln($) ≈ $601 average order
        'aov_sigma':             0.45,
        'churn_rate':            0.38,
        'active_recency_days':   (30,  400),
        'inactive_recency_days': (180, 1200),
    },

    # IT department, bulk device procurement for employees.
    # Very high AOV, high frequency, low churn.
    'Enterprise': {
        'weight':                0.08,
        'tenure_years':          (2.0, 6.0),
        'orders_per_year':       (3.5, 7.0),
        'aov_mu':                8.10,    # ln($) ≈ $3,294 average order (bulk)
        'aov_sigma':             0.55,
        'churn_rate':            0.05,
        'active_recency_days':   (10,   90),
        'inactive_recency_days': (400, 1000),
    },

    # Mac Pro/Studio buyer, buys Pro apps (Logic, Final Cut), high ASP.
    'Creator': {
        'weight':                0.06,
        'tenure_years':          (1.5, 6.0),
        'orders_per_year':       (2.0, 4.0),
        'aov_mu':                7.70,    # ln($) ≈ $2,208 average order
        'aov_sigma':             0.50,
        'churn_rate':            0.08,
        'active_recency_days':   (15,  180),
        'inactive_recency_days': (300,  900),
    },

    # Formerly active customers who switched ecosystem or went dormant.
    # Drives the At-Risk and Lost segments organically.
    'Former Customer': {
        'weight':                0.12,
        'tenure_years':          (0.5, 3.0),
        'orders_per_year':       (0.8, 2.0),
        'aov_mu':                6.20,    # ln($) ≈ $493 average order
        'aov_sigma':             0.50,
        'churn_rate':            0.93,    # almost all have churned
        'active_recency_days':   (90,  400),
        'inactive_recency_days': (365, 2000),
    },
}
# Weight sum: 0.10+0.19+0.12+0.11+0.22+0.08+0.06+0.12 = 1.00 ✓

# ─────────────────────────────────────────────────────────────────────
# SEGMENT-LEVEL PARAMETERS
# Applied AFTER segment is assigned from RFM scoring.
# Subscription and CLV are derived from the segment, not the persona,
# so they are internally consistent with the assigned tier.
# ─────────────────────────────────────────────────────────────────────
SEGMENT_SUB_PROB = {
    # Apple Services attach rate: ~55% overall device base.
    # Champions are power users of the ecosystem — near-universal adoption.
    'Champions':          0.93,
    'Loyal Customers':    0.82,
    'Potential Loyalists':0.65,
    'New Customers':      0.38,
    'Promising':          0.58,
    'Needs Attention':    0.42,
    'At Risk':            0.30,
    'Lost Customers':     0.12,
}

SEGMENT_CLV_RANGE = {
    # CLV multiplier applied to total_revenue_usd.
    # Reflects future expected value relative to historical spend.
    'Champions':          (3.5, 6.0),
    'Loyal Customers':    (2.5, 4.5),
    'Potential Loyalists':(1.8, 3.5),
    'New Customers':      (1.2, 2.5),
    'Promising':          (1.5, 3.0),
    'Needs Attention':    (1.0, 2.0),
    'At Risk':            (0.8, 1.5),
    'Lost Customers':     (0.5, 1.2),
}


# ═════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS — RFM PIPELINE
# These are pure functions that operate on DataFrames.
# They are intentionally separated from the DB-write function
# so they can be unit-tested independently.
# ═════════════════════════════════════════════════════════════════════

def _build_customer_profiles(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Stage 1: Generate raw behavioral profiles for n customers.

    For each customer:
      - Sample a persona according to population weights
      - Derive first_purchase_date from persona tenure
      - Decide active vs. churned (persona churn_rate)
      - Derive last_purchase_date from recency distribution
      - Derive total_orders from frequency × active years
      - Derive total_revenue_usd from log-normal AOV × orders

    No segment logic here — that comes after RFM scoring.
    """
    persona_names  = list(PERSONAS.keys())
    weights        = np.array([PERSONAS[p]['weight'] for p in persona_names])
    persona_idx    = rng.choice(len(persona_names), size=n, p=weights)

    rows = []
    max_back = (REFERENCE_DATE - PLATFORM_START).days   # hard ceiling on tenure

    for pi in persona_idx:
        pname = persona_names[pi]
        p     = PERSONAS[pname]

        # ── First purchase date ──────────────────────────────────────
        tenure_days = int(rng.uniform(*p['tenure_years']) * 365)
        tenure_days = min(tenure_days, max_back)
        first_dt    = REFERENCE_DATE - timedelta(days=tenure_days)

        # ── Last purchase date ───────────────────────────────────────
        churned = rng.random() < p['churn_rate']
        if churned:
            d_min, d_max = p['inactive_recency_days']
        else:
            d_min, d_max = p['active_recency_days']

        recency_days = int(rng.uniform(max(0, d_min), d_max))
        last_dt      = REFERENCE_DATE - timedelta(days=recency_days)

        # Clamp: first_dt ≤ last_dt ≤ REFERENCE_DATE
        last_dt  = min(max(last_dt, first_dt), REFERENCE_DATE)
        first_dt = min(first_dt, last_dt)

        # ── Order count ──────────────────────────────────────────────
        active_years = max(0.1, (last_dt - first_dt).days / 365.0)
        opr          = rng.uniform(*p['orders_per_year'])
        total_orders = int(np.clip(round(opr * active_years), 1, 100))

        # ── Revenue — log-normal AOV ─────────────────────────────────
        aov           = float(np.exp(rng.normal(p['aov_mu'], p['aov_sigma'])))
        aov           = float(np.clip(aov, 99.0, 9000.0))
        total_revenue = round(total_orders * aov, 2)

        rows.append({
            'persona':             pname,
            'first_purchase_date': first_dt,
            'last_purchase_date':  last_dt,
            'total_orders':        total_orders,
            'total_revenue_usd':   total_revenue,
        })

    return pd.DataFrame(rows)


def _compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 2: Compute raw RFM metrics.

    R = recency_days  (days since last purchase from REFERENCE_DATE)
    F = total_orders  (already in DataFrame)
    M = total_revenue_usd (already in DataFrame)
    """
    ref_ts          = pd.Timestamp(REFERENCE_DATE)
    df['recency_days'] = (
        ref_ts - pd.to_datetime(df['last_purchase_date'])
    ).dt.days.clip(lower=0)
    return df


def _score_rfm_quintiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 3: Score R, F, M into quintile bands 1–5.

    Scoring direction:
      R: lower recency_days  → higher score (bought most recently = 5)
      F: higher total_orders → higher score (most frequent  = 5)
      M: higher revenue      → higher score (highest spender = 5)

    Method: rank-based quintile (pct rank → cut into 5 equal bands).
    This is robust to any distribution shape and handles ties correctly.
    The composite rfm_score is R×100 + F×10 + M (range 111–555).
    """
    def quintile_score(series: pd.Series, invert: bool = False) -> pd.Series:
        """
        Map a numeric series to integer scores 1–5 via percentile rank.
        invert=True  → lower raw values get higher scores (used for Recency)
        invert=False → higher raw values get higher scores (used for F, M)
        """
        pct = series.rank(method='average', pct=True, na_option='bottom')
        if invert:
            pct = 1.0 - pct          # flip: smallest value → rank near 1.0

        # Cut into 5 equal-width percentile bands
        score = pd.cut(
            pct,
            bins=[-0.001, 0.20, 0.40, 0.60, 0.80, 1.001],
            labels=[1, 2, 3, 4, 5],
        ).astype('Int64').fillna(3).astype(int)
        return score

    df['r_score'] = quintile_score(df['recency_days'],    invert=True)
    df['f_score'] = quintile_score(df['total_orders'],    invert=False)
    df['m_score'] = quintile_score(df['total_revenue_usd'], invert=False)

    # Composite score — easy to display in the dashboard
    df['rfm_score'] = (
        df['r_score'] * 100 +
        df['f_score'] * 10  +
        df['m_score']
    )
    return df


def _assign_segment_from_rfm(
    r: int, f: int, m: int, seg_map: dict
) -> str:
    """
    Stage 4: Map (R, F, M) quintile scores to a segment name.

    Rules follow the standard CRM RFM segmentation framework
    (used in Salesforce Marketing Cloud, Braze, Amplitude, etc.).
    Priority order matters — first matching rule wins.

    Expected Apple-ecosystem distribution (approximate):
      Champions          ~14–17%   (R≥4, F≥4, M≥4)
      Loyal Customers    ~18–22%   (R≥3, F≥3, M≥3)
      Potential Loyalists~11–14%   (R≥4, F∈[2,3])
      New Customers       ~4–6%   (R=5, F=1)
      Promising           ~7–10%   (R≥3, F=2, M≥2)
      Needs Attention    ~10–14%   (catch-all for middle tier)
      At Risk             ~7–11%   (R≤2, F≥3 or M≥4)
      Lost Customers      ~5–8%   (R=1, F≤2, M≤3)
    """
    # ── Tier 1: Best customers in all three dimensions ───────────────
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'

    # ── Tier 2: Consistent, recent, high-value ───────────────────────
    if r >= 3 and f >= 3 and m >= 3:
        return 'Loyal Customers'

    # ── Tier 3: Recent buyers not yet at full loyalty ────────────────
    # Just joined — very recent, very low frequency
    if r == 5 and f == 1:
        return 'New Customers'

    # Recent, building frequency — classic "growth" segment
    if r >= 4 and 2 <= f <= 3:
        return 'Potential Loyalists'

    # Decent recency, started repeating — needs a nudge
    if r >= 3 and f == 2 and m >= 2:
        return 'Promising'

    # ── Tier 4: Declining engagement ────────────────────────────────
    # Were good customers; recency has fallen sharply
    if r <= 2 and (f >= 3 or m >= 4):
        return 'At Risk'

    # Very inactive, low historical engagement
    if r == 1 and f <= 2 and m <= 3:
        return 'Lost Customers'

    # ── Tier 5: Middle — mixed signals, needs monitoring ────────────
    return 'Needs Attention'


# ═════════════════════════════════════════════════════════════════════
# MAIN SEEDING FUNCTION — REDESIGNED
# ═════════════════════════════════════════════════════════════════════

def seed_fact_customer(conn, n: int = 50_000) -> None:
    """
    Production-grade synthetic customer analytics pipeline.

    ┌──────────────────────────────────────────────────────────────┐
    │  PIPELINE OVERVIEW                                           │
    │                                                              │
    │  Stage 1  Sample personas (Power User, Loyal Upgrader, …)   │
    │  Stage 2  Simulate purchase history per persona              │
    │  Stage 3  Compute RFM raw metrics from simulated history     │
    │  Stage 4  Score R, F, M using quintiles (equal 20% bands)   │
    │  Stage 5  Assign segment via standard CRM decision rules     │
    │  Stage 6  Derive is_subscriber + CLV from assigned segment   │
    │  Stage 7  Assign region, cohort, customer ID                 │
    │  Stage 8  Bulk-insert to fact_customer (batches of 5,000)    │
    └──────────────────────────────────────────────────────────────┘

    Key design properties:
    - No segment percentages are hard-coded anywhere.
      The distribution emerges from behavioral simulation + RFM math.
    - Subscription status and CLV are derived from the ASSIGNED SEGMENT,
      not the persona, so they are internally consistent.
    - All 50,000 customers are generated in-memory as a single DataFrame
      before any DB writes, enabling fast vectorized operations.
    - The random seed (42) makes the output fully reproducible.
    """
    rng    = np.random.default_rng(42)
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE fact_customer RESTART IDENTITY CASCADE")
    conn.commit()

    # ── Fetch dimension keys ─────────────────────────────────────────
    cursor.execute("SELECT region_key, region_name FROM dim_region")
    region_rows  = cursor.fetchall()
    region_keys  = [r[0] for r in region_rows]
    region_names = [r[1] for r in region_rows]

    # Regional allocation weights (Apple FY2025 geographic disclosure)
    REG_WEIGHTS_MAP = {
        'Americas':             0.429,
        'Europe':               0.267,
        'China':                0.155,
        'Japan':                0.069,
        'Rest of Asia Pacific': 0.080,
    }
    reg_w = np.array([REG_WEIGHTS_MAP.get(rn, 0.05) for rn in region_names],
                     dtype=float)
    reg_w /= reg_w.sum()   # normalise to exactly 1.0

    cursor.execute("SELECT segment_key, segment_name FROM dim_customer_segment")
    seg_rows = cursor.fetchall()
    seg_map  = {r[1]: r[0] for r in seg_rows}   # segment_name → segment_key

    # ── Stage 1–2: Simulate behavioral profiles ──────────────────────
    print(f"  [1/5] Simulating {n:,} customer behavioral profiles...")
    df = _build_customer_profiles(n, rng)

    # ── Stage 3: Compute RFM raw metrics ────────────────────────────
    print(f"  [2/5] Computing RFM metrics (R=recency, F=frequency, M=monetary)...")
    df = _compute_rfm(df)

    # ── Stage 4: Quintile scoring ───────────────────────────────────
    print(f"  [3/5] Scoring R, F, M into quintiles (5 equal 20% bands)...")
    df = _score_rfm_quintiles(df)

    # ── Stage 5: Segment assignment ─────────────────────────────────
    print(f"  [4/5] Assigning segments from RFM scores (CRM decision rules)...")
    df['segment_name'] = df.apply(
        lambda row: _assign_segment_from_rfm(
            row['r_score'], row['f_score'], row['m_score'], seg_map
        ),
        axis=1
    )
    df['segment_key'] = df['segment_name'].map(seg_map)

    # Guard: any unmapped segments → Needs Attention
    fallback_key = seg_map.get('Needs Attention', list(seg_map.values())[0])
    df['segment_key'] = df['segment_key'].fillna(fallback_key).astype(int)

    # ── Stage 6: Derive subscription status and CLV from segment ────
    sub_probs = df['segment_name'].map(SEGMENT_SUB_PROB).fillna(0.5)
    df['is_subscriber'] = rng.random(n) < sub_probs.values

    clv_lo = df['segment_name'].map(
        {k: v[0] for k, v in SEGMENT_CLV_RANGE.items()}
    ).fillna(1.0).astype(float)
    clv_hi = df['segment_name'].map(
        {k: v[1] for k, v in SEGMENT_CLV_RANGE.items()}
    ).fillna(2.0).astype(float)
    multipliers = rng.uniform(0, 1, n) * (clv_hi.values - clv_lo.values) + clv_lo.values
    df['clv_estimated_usd'] = (df['total_revenue_usd'] * multipliers).round(2)

    # ── Stage 7: Region, cohort, customer ID ─────────────────────────
    df['region_key'] = rng.choice(region_keys, size=n, p=reg_w)

    def _cohort(d: date) -> str:
        m = d.month
        if   m >= 10: return f"FY{d.year+1}-Q1"
        elif m <=  3: return f"FY{d.year}-Q2"
        elif m <=  6: return f"FY{d.year}-Q3"
        else:         return f"FY{d.year}-Q4"

    df['cohort_quarter'] = [
        _cohort(d) for d in pd.to_datetime(df['first_purchase_date']).dt.date
    ]
    df['customer_id'] = [f"CUST-{i:06d}" for i in range(1, n + 1)]

    # ── Print organic distribution ───────────────────────────────────
    print(f"\n  Segment distribution (organic — no percentages were hard-coded):")
    print(f"  {'Segment':<25} {'Count':>7}  {'%':>6}  Distribution")
    print(f"  {'─'*65}")
    dist = (df['segment_name']
            .value_counts()
            .reindex(['Champions', 'Loyal Customers', 'Potential Loyalists',
                      'New Customers', 'Promising', 'Needs Attention',
                      'At Risk', 'Lost Customers'], fill_value=0)
            .reset_index())
    dist.columns = ['Segment', 'Count']
    dist['pct']  = dist['Count'] / n * 100
    for _, row in dist.iterrows():
        bar = '█' * int(row['pct'] / 2)
        print(f"  {row['Segment']:<25} {row['Count']:>7,}  "
              f"{row['pct']:>5.1f}%  {bar}")
    print()

    # ── Stage 8: Bulk-insert to DB ───────────────────────────────────
    cols = [
        'customer_id', 'first_purchase_date', 'last_purchase_date',
        'total_revenue_usd', 'total_orders', 'region_key', 'segment_key',
        'cohort_quarter', 'is_subscriber', 'rfm_score', 'clv_estimated_usd',
    ]
    records = list(df[cols].itertuples(index=False, name=None))
    BATCH   = 5_000
    print(f"  [5/5] Inserting {n:,} rows to fact_customer in batches of {BATCH:,}...")

    for start_idx in range(0, len(records), BATCH):
        cursor.executemany("""
            INSERT INTO fact_customer
            (customer_id, first_purchase_date, last_purchase_date,
             total_revenue_usd, total_orders, region_key, segment_key,
             cohort_quarter, is_subscriber, rfm_score, clv_estimated_usd)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, records[start_idx:start_idx + BATCH])
        conn.commit()
        done = min(start_idx + BATCH, n)
        print(f"    → {done:,} / {n:,} inserted")

    # Export synthetic data for external tooling / Power BI direct file
    os.makedirs('data/synthetic', exist_ok=True)
    df.to_csv('data/synthetic/customer_export.csv', index=False)
    print(f"\n✓ fact_customer: {n:,} rows | "
          f"exported to data/synthetic/customer_export.csv")


# ─────────────────────────────────────────────────────────────────────
# DATABASE HELPERS — unchanged from original
# ─────────────────────────────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def seed_dim_date(conn):
    cursor = conn.cursor()
    records = []
    for fy in range(2020, 2027):
        max_q = 1 if fy == 2026 else 4
        for fq in range(1, max_q + 1):
            month_start  = {1:10, 2:1, 3:4, 4:7}[fq]
            cal_year     = fy - 1 if fq == 1 else fy
            quarter_date = date(cal_year, month_start, 1)
            label        = f"FY{fy} Q{fq}"
            is_current   = (fy == 2026 and fq == 1)
            records.append((quarter_date, fy, fq,
                            quarter_date.year, quarter_date.month,
                            label, is_current))
    cursor.executemany("""
        INSERT INTO dim_date
        (full_date,fiscal_year,fiscal_quarter,calendar_year,
         calendar_month,quarter_label,is_current_qtr)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, records)
    conn.commit()
    print(f"✓ dim_date: {len(records)} quarters (FY2020–FY2026 Q1)")


def seed_dim_product(conn):
    cursor = conn.cursor()
    products = [
        ("iPhone",           "Hardware", 2007, True, "High"),
        ("Mac",              "Hardware", 1984, True, "Medium"),
        ("iPad",             "Hardware", 2010, True, "Medium"),
        ("Wearables & Home", "Hardware", 2015, True, "Medium"),
        ("Services",         "Services", 2016, True, "High"),
        ("Accessories",      "Hardware", 2001, True, "Low"),
    ]
    cursor.executemany("""
        INSERT INTO dim_product
        (product_name,product_category,launch_year,is_active,gross_margin_tier)
        VALUES (%s,%s,%s,%s,%s)
    """, products)
    conn.commit()
    print(f"✓ dim_product: {len(products)} products")


def seed_dim_region(conn):
    cursor = conn.cursor()
    regions = [
        ("Americas",             "AMR",  "USD", False),
        ("Europe",               "EUR",  "EUR", False),
        ("China",                "CHN",  "CNY", True),
        ("Japan",                "JPN",  "JPY", False),
        ("Rest of Asia Pacific", "APAC", "USD", True),
    ]
    cursor.executemany("""
        INSERT INTO dim_region
        (region_name,region_code,currency_primary,is_high_growth)
        VALUES (%s,%s,%s,%s)
    """, regions)
    conn.commit()
    print(f"✓ dim_region: {len(regions)} regions")


def seed_dim_customer_segment(conn):
    cursor = conn.cursor()
    segments = [
        ("Champions",           "Top",     "High"),
        ("Loyal Customers",     "High",    "High"),
        ("Potential Loyalists", "Medium",  "Medium"),
        ("New Customers",       "New",     "Low"),
        ("Promising",           "Medium",  "Medium"),
        ("Needs Attention",     "Low",     "Medium"),
        ("At Risk",             "Low",     "High"),
        ("Lost Customers",      "Churned", "Low"),
    ]
    cursor.executemany("""
        INSERT INTO dim_customer_segment
        (segment_name,rfm_tier,revenue_band)
        VALUES (%s,%s,%s)
    """, segments)
    conn.commit()
    print(f"✓ dim_customer_segment: {len(segments)} segments")


def seed_fact_revenue(conn):
    """
    Inserts quarterly revenue data with regional splits.
    Regional noise is applied and then normalised so that
    the sum across regions exactly equals the product total.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT date_key,fiscal_year,fiscal_quarter FROM dim_date")
    date_map = {(r[1], r[2]): r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT product_key,product_name FROM dim_product")
    product_map = {r[1]: r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT region_key,region_name FROM dim_region")
    region_map = {r[1]: r[0] for r in cursor.fetchall()}

    asp_map = {
        "iPhone": 950, "Mac": 1500, "iPad": 550,
        "Wearables & Home": 350, "Services": 0, "Accessories": 130,
    }
    rng     = np.random.default_rng(42)
    records = []

    for (fy, fq, product), total_b in APPLE_REVENUE_DATA.items():
        date_key    = date_map.get((fy, fq))
        product_key = product_map.get(product)
        if not date_key or not product_key:
            continue

        margin  = PRODUCT_MARGINS.get(product, 0.38)
        total_m = total_b * 1000   # billions → millions
        splits  = REGIONAL_SPLITS_BY_YEAR.get(fy, REGIONAL_SPLITS_BY_YEAR[2025])

        # Apply per-region noise then normalise so regional sum = total_m
        raw_allocs = {}
        for region_name, split_pct in splits.items():
            noise = rng.uniform(-0.015, 0.015)
            raw_allocs[region_name] = max(0.001, split_pct + noise)

        alloc_sum = sum(raw_allocs.values())

        for region_name, raw in raw_allocs.items():
            region_key = region_map.get(region_name)
            if not region_key:
                continue

            # Normalise: this region gets exactly (raw/sum) × total_m
            region_rev   = round(total_m * raw / alloc_sum, 2)
            gross_profit = round(region_rev * margin, 2)
            asp          = asp_map.get(product, 0)
            units        = round(region_rev / asp, 4) if asp > 0 else 0.0

            records.append((
                date_key, product_key, region_key,
                region_rev, units, asp,
                round(margin * 100, 2),
                gross_profit, None,
            ))

    cursor.executemany("""
        INSERT INTO fact_revenue
        (date_key,product_key,region_key,revenue_usd_millions,
         units_millions,asp_usd,gross_margin_pct,
         gross_profit_usd_millions,yoy_growth_pct)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, records)
    conn.commit()
    print(f"✓ fact_revenue: {len(records)} rows | FY2022 Q1 → FY2026 Q1")


if __name__ == '__main__':
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM fact_revenue")
    existing = cursor.fetchone()[0]
    if existing > 0:
        print(f"\n⛔  STOPPED: fact_revenue already has {existing:,} rows.")
        print("    TRUNCATE all tables first, then re-run.")
        conn.close()
        exit(1)

    print("✓ Tables are empty. Starting seed pipeline...\n")
    seed_dim_date(conn)
    seed_dim_product(conn)
    seed_dim_region(conn)
    seed_dim_customer_segment(conn)
    seed_fact_revenue(conn)
    seed_fact_customer(conn)
    conn.close()

    print("\n✅ Database seeded. FY2022–FY2026 Q1 | 50,000 customers")
    print("⚠  Do NOT run again without TRUNCATING first.")