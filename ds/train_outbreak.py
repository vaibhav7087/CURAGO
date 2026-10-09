"""
ds/train_outbreak.py — IsolationForest outbreak detection.
Tries ds/data/raw/district_weekly_cases.csv, falls back to synthetic districts.
Outputs: models/outbreak_iso.pkl, models/outbreak_features.json
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent
MODEL_DIR = HERE / "models"
RAW = HERE / "data" / "raw" / "district_weekly_cases.csv"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_or_synthesize():
    if RAW.exists():
        print(f"Loading {RAW}")
        return pd.read_csv(RAW)
    print("No district CSV — synthesizing 6 districts x 104 weeks...")
    rng = np.random.default_rng(42)
    districts = ["Ernakulam", "Kozhikode", "Rampur", "Dharampur", "Panvel", "Alibaug"]
    weeks = pd.date_range("2023-01-02", periods=104, freq="W-MON")
    rows = []
    for d in districts:
        base = rng.integers(3, 12)
        for w in weeks:
            seasonal = 4 * np.sin(2 * np.pi * w.isocalendar().week / 52)
            cases = max(0, int(base + seasonal + rng.normal(0, 3)))
            # Inject 2 known outbreak spikes
            if d in ("Ernakulam", "Kozhikode") and "2024-05-20" <= str(w.date()) <= "2024-06-10":
                cases += 25
            rows.append({"district": d, "week": w.strftime("%Y-%m-%d"),
                         "case_count": cases, "disease": "Dengue"})
    return pd.DataFrame(rows)


def main():
    from sklearn.ensemble import IsolationForest
    df = load_or_synthesize().sort_values(["district", "week"]).copy()
    df["rolling_mean"] = df.groupby("district")["case_count"].transform(
        lambda x: x.rolling(4, min_periods=1).mean())
    df["rolling_std"] = df.groupby("district")["case_count"].transform(
        lambda x: x.rolling(4, min_periods=1).std().fillna(0))
    df["week_of_year"] = pd.to_datetime(df["week"]).dt.isocalendar().week.astype(int)
    df["ratio_to_mean"] = df["case_count"] / df["rolling_mean"].clip(lower=1)
    features = ["case_count", "rolling_mean", "rolling_std", "week_of_year", "ratio_to_mean"]
    X = df[features].fillna(0)
    iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
    df["anomaly_score"] = iso.fit_predict(X)
    df["is_outbreak"] = (df["anomaly_score"] == -1).astype(int)
    print(f"Flagged outbreaks: {int(df['is_outbreak'].sum())}/{len(df)}")
    print(df[df["is_outbreak"] == 1].head(10).to_string())
    import json
    joblib.dump(iso, MODEL_DIR / "outbreak_iso.pkl")
    with open(MODEL_DIR / "outbreak_features.json", "w") as f:
        json.dump(features, f)
    print("Saved outbreak_iso.pkl + outbreak_features.json")


if __name__ == "__main__":
    main()
