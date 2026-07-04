# run_full_pipeline.py
"""
Master pipeline runner.
Executes every analytics module in the correct order,
then launches the Streamlit dashboard.

Run from the project root:
    python run_full_pipeline.py
"""
import subprocess
import sys
import os
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))


def run_step(label: str, script_path: str) -> bool:
    """Run a Python script as a subprocess and report success/failure."""
    full_path = os.path.join(ROOT, script_path)
    if not os.path.exists(full_path):
        print(f"  ⚠  Skipped (file not found): {script_path}")
        return True

    start = time.time()
    result = subprocess.run(
        [sys.executable, full_path],
        capture_output=False,
        cwd=ROOT
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"  ✓  Completed in {elapsed:.1f}s")
        return True
    else:
        print(f"  ✗  FAILED after {elapsed:.1f}s — check output above")
        return False


def create_export_dirs():
    """Ensure all export directories exist."""
    dirs = [
        "exports/charts",
        "exports/reports",
        "exports/ai_narratives",
        "data/processed",
        "data/synthetic",
    ]
    for d in dirs:
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    print("  ✓  Export directories ready")


def main():
    print("\n" + "═" * 60)
    print(f"  Apple Global Performance Analysis — PIPELINE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    # Step 0: directories
    print("\n── Step 0: Setup")
    create_export_dirs()

    # Step 1: Analytics modules (order matters)
    steps = [
        ("Margin Analysis",             "analytics/margin_analysis.py"),
        ("RFM Customer Segmentation",   "analytics/rfm_analysis.py"),
        ("Revenue Forecasting",         "analytics/forecasting.py"),
        ("Cohort & Retention Analysis", "analytics/cohort_analysis.py"),
    ]

    all_ok = True
    for i, (label, script) in enumerate(steps, 1):
        print(f"\n── Step {i}: {label}")
        ok = run_step(label, script)
        if not ok:
            all_ok = False

    # Step 2: Export standalone dashboard
    print("\n── Step 5: Export HTML Dashboard")
    run_step("HTML Dashboard Export", "visualizations/dashboard.py")

    # Final status
    print("\n" + "═" * 60)
    if all_ok:
        print("  ✅  Pipeline complete — all steps succeeded")
    else:
        print("  ⚠   Pipeline finished with errors — check output above")

    print("\n  Next steps:")
    print("  1. Open exports/reports/apple_dashboard.html in browser")
    print("  2. Run Streamlit app: streamlit run app.py")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()