"""
ds/train_forecast.py — Demand forecast (notebook-only, no pkl).
Tries ds/data/raw/salesmonthly.csv, falls back to synthetic 8-drug monthly series.
Outputs: models/demand_forecast_comparison.png, models/demand_forecast_metrics.csv
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent
MODEL_DIR = HERE / "models"
RAW = HERE / "data" / "raw" / "salesmonthly.csv"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DRUGS = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]


def load_or_synthesize():
    if RAW.exists():
        print(f"Loading {RAW}")
        df = pd.read_csv(RAW)
        # Normalize date col
        for cand in ["datum", "date", "Date", "DATUM"]:
            if cand in df.columns:
                df["date"] = pd.to_datetime(df[cand])
                break
        if "date" not in df.columns:
            raise ValueError(f"No date column in {list(df.columns)}")
        df = df.sort_values("date")
        missing = [d for d in DRUGS if d not in df.columns]
        if missing:
            print(f"Missing drug cols {missing}, synthesizing those...")
            rng = np.random.default_rng(42)
            idx = pd.to_datetime(df["date"])
            for d in missing:
                df[d] = 100 + 10 * np.sin(2 * np.pi * idx.dt.month / 12) + rng.normal(0, 8, len(df))
        return df[["date"] + DRUGS]
    print("No salesmonthly.csv — synthesizing 8-drug monthly series (2019-2026)...")
    rng = np.random.default_rng(42)
    dates = pd.date_range("2019-01-01", "2026-09-01", freq="MS")
    data = {"date": dates}
    for i, d in enumerate(DRUGS):
        trend = np.linspace(80, 140 + i * 6, len(dates))
        seas = 18 * np.sin(2 * np.pi * (dates.month + i) / 12)
        noise = rng.normal(0, 7, len(dates))
        data[d] = np.maximum(5, trend + seas + noise).round(1)
    return pd.DataFrame(data)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from lightgbm import LGBMRegressor
    from sklearn.metrics import mean_absolute_error

    df = load_or_synthesize()
    print(df.head().to_string())
    print(df.shape, df.columns.tolist())

    results = []
    fig, axes = plt.subplots(4, 2, figsize=(16, 20))
    axes = axes.flatten()
    for idx, drug in enumerate(DRUGS):
        series = df.set_index("date")[drug].dropna().asfreq("MS")
        train, test = series[:-12], series[-12:]

        naive_pred = train[-12:].values
        mae_naive = mean_absolute_error(test, naive_pred)

        try:
            hw = ExponentialSmoothing(train, seasonal="add", seasonal_periods=12).fit(optimized=True, use_brute=True)
            hw_pred = np.asarray(hw.forecast(12))
            mae_hw = mean_absolute_error(test, hw_pred)
        except Exception as e:
            print(f"{drug} HW failed ({e}), using naive")
            hw_pred, mae_hw = naive_pred, mae_naive

        def make_lag(s, n_lags=12):
            d = pd.DataFrame({"y": s})
            for lag in range(1, n_lags + 1):
                d[f"lag_{lag}"] = d["y"].shift(lag)
            d["month"] = d.index.month
            return d.dropna()

        dfl = make_lag(series)
        X, y = dfl.drop(columns=["y"]), dfl["y"]
        Xtr, ytr, Xte, yte = X[:-12], y[:-12], X[-12:], y[-12:]
        lgb = LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)
        lgb.fit(Xtr, ytr)
        lgb_pred = lgb.predict(Xte)
        mae_lgb = mean_absolute_error(yte, lgb_pred)

        results.append({"Drug (ATC)": drug, "MAE Seasonal Naive": round(float(mae_naive), 2),
                        "MAE Holt-Winters": round(float(mae_hw), 2), "MAE LightGBM": round(float(mae_lgb), 2)})
        ax = axes[idx]
        ax.plot(test.index, test.values, "k-", label="Actual", linewidth=2)
        ax.plot(test.index, hw_pred, "b--", label=f"HW (MAE={mae_hw:.1f})")
        ax.plot(test.index, lgb_pred, "r--", label=f"LGB (MAE={mae_lgb:.1f})")
        ax.set_title(drug)
        ax.legend(fontsize=8)
        ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(MODEL_DIR / "demand_forecast_comparison.png", dpi=150)
    plt.close()
    rdf = pd.DataFrame(results)
    print("\nDEMAND FORECAST METRICS:")
    try:
        print(rdf.to_markdown(index=False))
    except Exception:
        print(rdf.to_string(index=False))
    rdf.to_csv(MODEL_DIR / "demand_forecast_metrics.csv", index=False)
    print("Saved demand_forecast_comparison.png + demand_forecast_metrics.csv")


if __name__ == "__main__":
    main()
