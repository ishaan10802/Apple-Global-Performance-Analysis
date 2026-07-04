# diagnose_schema.py
# Run this once from your project root (same place you run `streamlit run app.py`):
#     python diagnose_schema.py
# Paste the output back to Claude so all the KeyError / AttributeError
# issues can be fixed in one pass instead of one crash at a time.

import sys, os
sys.path.append(os.path.dirname(__file__))

from analytics.db_connector import query

VIEWS = [
    "vw_executive_summary",
    "vw_product_margin",
    "vw_regional_kpi",
    "vw_services_growth",
]

print("=" * 60)
print("DATABASE VIEW COLUMNS")
print("=" * 60)
for v in VIEWS:
    try:
        df = query(f"SELECT * FROM {v} LIMIT 1")
        print(f"\n[{v}]")
        print(df.columns.tolist())
    except Exception as e:
        print(f"\n[{v}] -> ERROR: {e}")

print()
print("=" * 60)
print("ANALYTICS FUNCTION RETURN STRUCTURES")
print("=" * 60)

def describe_dict(name, d):
    print(f"\n[{name}]")
    if not isinstance(d, dict):
        print(f"  (not a dict -> {type(d)})")
        return
    for k, v in d.items():
        extra = ""
        if hasattr(v, "shape"):
            extra = f" shape={v.shape}"
        if hasattr(v, "columns"):
            extra += f" columns={list(v.columns)}"
        print(f"  {k}: {type(v).__name__}{extra}")

try:
    from analytics.cohort_analysis import run_cohort
    describe_dict("run_cohort()", run_cohort())
except Exception as e:
    print(f"\n[run_cohort()] -> ERROR: {e}")

try:
    from analytics.rfm_analysis import run_rfm
    describe_dict("run_rfm()", run_rfm())
except Exception as e:
    print(f"\n[run_rfm()] -> ERROR: {e}")

try:
    from analytics.margin_analysis import run_margin
    describe_dict("run_margin()", run_margin())
except Exception as e:
    print(f"\n[run_margin()] -> ERROR: {e}")

try:
    from analytics.forecasting import run_forecasts
    fc = run_forecasts(periods=6)
    describe_dict("run_forecasts()", fc)
    if isinstance(fc, dict) and "by_product" in fc:
        bp = fc["by_product"]
        print(f"  by_product keys: {list(bp.keys())}")
        first_key = next(iter(bp), None)
        if first_key is not None:
            print(f"  by_product['{first_key}'] columns: {list(bp[first_key].columns)}")
except Exception as e:
    print(f"\n[run_forecasts()] -> ERROR: {e}")

print()
print("Done. Copy everything above and share it back.")    