# analytics/forecasting.py

import os
import sys
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from analytics.db_connector import query


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_series():
    return query("""
        SELECT
            fiscal_year,
            fiscal_quarter,
            quarter_label,
            product_name,
            SUM(revenue_usd_millions) AS revenue_m
        FROM vw_yoy_revenue
        GROUP BY
            fiscal_year,
            fiscal_quarter,
            quarter_label,
            product_name
        ORDER BY
            fiscal_year,
            fiscal_quarter
    """)


# ---------------------------------------------------------
# BUILD SEASONAL INDICES
# ---------------------------------------------------------

def calculate_seasonality(df):
    """
    Compute average quarter seasonality.

    Example:
        Q1 = 1.32
        Q2 = 0.91
        Q3 = 0.86
        Q4 = 0.91

    Captures Apple's holiday season effect.
    """

    overall_avg = df["revenue_m"].mean()

    seasonal = (
        df.groupby("fiscal_quarter")["revenue_m"]
          .mean()
          / overall_avg
    )

    return seasonal.to_dict()


# ---------------------------------------------------------
# FORECAST SINGLE PRODUCT
# ---------------------------------------------------------

def forecast_product(df_p, periods=6):

    df = (
        df_p.sort_values(
            ["fiscal_year", "fiscal_quarter"]
        )
        .copy()
        .reset_index(drop=True)
    )

    # Time index
    df["t"] = np.arange(len(df))

    # -----------------------------------------------------
    # Seasonality
    # -----------------------------------------------------

    seasonality = calculate_seasonality(df)

    df["season_factor"] = (
        df["fiscal_quarter"]
        .map(seasonality)
    )

    df["deseasonalized"] = (
        df["revenue_m"]
        / df["season_factor"]
    )

    # -----------------------------------------------------
    # Train / Test Split
    # -----------------------------------------------------

    if len(df) >= 10:
        train = df.iloc[:-3]
        test = df.iloc[-3:]
    else:
        train = df
        test = df.iloc[-2:]

    # -----------------------------------------------------
    # Trend Model
    # -----------------------------------------------------

    model = LinearRegression()

    model.fit(
        train[["t"]],
        train["deseasonalized"]
    )

    # -----------------------------------------------------
    # Honest Holdout MAPE
    # -----------------------------------------------------

    pred_deseason = model.predict(
        test[["t"]]
    )

    pred_actual = (
        pred_deseason
        * test["season_factor"]
    )

    mape = (
        mean_absolute_percentage_error(
            test["revenue_m"],
            pred_actual
        )
        * 100
    )

    # -----------------------------------------------------
    # Refit on Full Data
    # -----------------------------------------------------

    model.fit(
        df[["t"]],
        df["deseasonalized"]
    )

    # -----------------------------------------------------
    # Future Periods
    # -----------------------------------------------------

    future_t = np.arange(
        len(df),
        len(df) + periods
    )

    fy = int(df["fiscal_year"].iloc[-1])
    fq = int(df["fiscal_quarter"].iloc[-1])

    labels = []
    future_quarters = []

    for _ in range(periods):

        fq += 1

        if fq > 4:
            fq = 1
            fy += 1

        labels.append(
            f"FY{fy} Q{fq}"
        )

        future_quarters.append(fq)

    # -----------------------------------------------------
    # Trend Forecast
    # -----------------------------------------------------

    trend_forecast = model.predict(
        future_t.reshape(-1, 1)
    )

    seasonal_factors = np.array([
        seasonality[q]
        for q in future_quarters
    ])

    forecast = (
        trend_forecast
        * seasonal_factors
    )

    # -----------------------------------------------------
    # Confidence Interval
    # -----------------------------------------------------

    residuals = (
        train["deseasonalized"]
        - model.predict(train[["t"]])
    )

    std_error = residuals.std()

    ci = (
        1.96
        * std_error
        * seasonal_factors
    )

    # -----------------------------------------------------
    # Historical
    # -----------------------------------------------------

    hist = df[
        ["quarter_label", "revenue_m"]
    ].copy()

    hist["type"] = "Actual"
    hist["lo"] = np.nan
    hist["hi"] = np.nan

    # -----------------------------------------------------
    # Forecast
    # -----------------------------------------------------

    fore = pd.DataFrame({

        "quarter_label": labels,

        "revenue_m": np.round(
            forecast,
            2
        ),

        "type": "Forecast",

        "lo": np.round(
            forecast - ci,
            2
        ),

        "hi": np.round(
            forecast + ci,
            2
        )
    })

    out = pd.concat(
        [hist, fore],
        ignore_index=True
    )

    out["product_name"] = (
        df_p["product_name"]
        .iloc[0]
    )

    out["mape"] = round(
        float(mape),
        1
    )

    return out


# ---------------------------------------------------------
# RUN ALL FORECASTS
# ---------------------------------------------------------

def run_forecasts(periods=6):

    df = load_series()

    results = {}

    for product in df["product_name"].unique():

        sub = (
            df[
                df["product_name"]
                == product
            ]
            .copy()
        )

        if len(sub) >= 8:

            results[product] = (
                forecast_product(
                    sub,
                    periods
                )
            )

    combined = pd.concat(
        results.values(),
        ignore_index=True
    )

    output_dir = (
        "../data/processed"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    combined.to_csv(
        os.path.join(
            output_dir,
            "forecast_results.csv"
        ),
        index=False
    )

    return {
        "by_product": results,
        "combined": combined
    }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    forecasts = run_forecasts()

    print("\nForecast Accuracy\n")

    for product, df_p in forecasts["by_product"].items():

        print(
            f"{product}: "
            f"MAPE = "
            f"{df_p['mape'].iloc[0]:.1f}%"
        )