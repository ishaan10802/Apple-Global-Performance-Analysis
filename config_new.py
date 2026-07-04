


# config_new.py
# Cloud-ready configuration file.
# This version reads from environment variables for deployment
# and falls back to direct values for local development.
# Rename this to config.py or import from here as needed.

import os
from dotenv import load_dotenv

load_dotenv()

# ── Database Configuration ────────────────────────────────────────
# For LOCAL development: fill in values directly below
# For CLOUD deployment: set as environment variables in Streamlit Cloud

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME",     "apple_intelligence"),
    "user":     os.environ.get("DB_USER",     "postgres"),
    "password": os.environ.get("DB_PASSWORD")
}
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")     

OPENAI_MODEL   = "gpt-4o"
MAX_TOKENS     = 1000

# ── Apple Business Constants ──────────────────────────────────────
PRODUCT_LINES = [
    "iPhone",
    "Mac",
    "iPad",
    "Wearables & Home",
    "Services",
    "Accessories",
]

REGIONS = [
    "Americas",
    "Europe",
    "China",
    "Japan",
    "Rest of Asia Pacific",
]

# Apple fiscal year starts in October
FISCAL_YEAR_START_MONTH = 10

# ── Data Coverage ─────────────────────────────────────────────────
DATA_START_FY   = 2022
DATA_END_FY     = 2026
DATA_END_Q      = 1          # FY2026 Q1 is the latest complete quarter
TOTAL_CUSTOMERS = 50_000

# ── Export Paths ──────────────────────────────────────────────────
EXPORT_CHARTS     = "exports/charts"
EXPORT_REPORTS    = "exports/reports"
EXPORT_NARRATIVES = "exports/ai_narratives"

# ── App Settings ──────────────────────────────────────────────────
APP_TITLE       = "Apple Global Performance Analysis Platform"
APP_SUBTITLE    = "Enterprise Analytics · FY2022–FY2026 Q1"
APP_ICON        = "🍎"
CACHE_TTL_SECS  = 600          # 10 minutes

# ── Brand Colors (Apple dark theme) ──────────────────────────────
COLORS = {
    "blue":    "#0071E3",
    "green":   "#30D158",
    "orange":  "#FF9F0A",
    "red":     "#FF453A",
    "purple":  "#BF5AF2",
    "gray":    "#6E6E73",
    "bg":      "#1C1C1E",
    "card":    "#2C2C2E",
    "text":    "#F5F5F7",
    "muted":   "#98989D",
    "border":  "rgba(255,255,255,0.06)",
}

PRODUCT_COLORS = {
    "iPhone":           COLORS["blue"],
    "Services":         COLORS["green"],
    "Mac":              COLORS["orange"],
    "iPad":             COLORS["purple"],
    "Wearables & Home": COLORS["red"],
    "Accessories":      COLORS["gray"],
}

REGION_COLORS = [
    COLORS["blue"],
    COLORS["green"],
    COLORS["orange"],
    COLORS["purple"],
    COLORS["red"],
]