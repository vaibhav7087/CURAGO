"""
ds/predict.py — Inference functions for Curago DS models.
Imported by backend/app/routers/predict.py and webhook.py.

All functions are pure Python + sklearn/xgboost — no network calls.
"""
import os
import json
import joblib
import numpy as np
from pathlib import Path

# --- Model Loading ---
MODEL_DIR = Path(__file__).parent / "models"
# DS_DATA_MODE: 'synthetic' (default, stable stage demo) or 'real' (Symptom2Disease model).
# Read live via env each call so demo can flip without restart.
_triage_model = None
_triage_features = None
_disease_model = None


def data_mode() -> str:
    return os.getenv("DS_DATA_MODE", "synthetic")


def _load_triage_model():
    global _triage_model, _triage_features
    if _triage_model is None:
        pkl_path = MODEL_DIR / "triage.pkl"
        feat_path = MODEL_DIR / "triage_features.json"
        if pkl_path.exists():
            _triage_model = joblib.load(pkl_path)
            with open(feat_path) as f:
                _triage_features = json.load(f)
            print(f"Triage model loaded: {len(_triage_features)} features")
        else:
            print(f"Triage model not found at {pkl_path}")
    return _triage_model, _triage_features


def predict_severity(patient_data: dict) -> dict:
    """
    Predict triage severity from patient data.

    Input patient_data keys (all optional, missing -> NaN):
        - age: int
        - gender: str ("Male"/"Female")
        - symptoms: str (comma-separated symptom text)
        - temperature: float (Fahrenheit)
        - pulse: int
        - respiratory_rate: int
        - bp_systolic: int
        - bp_diastolic: int
        - spo2: float (pulse oximetry %)
        - pain_scale: int (0-10)

    Returns:
        {
            "predicted_severity": "High" | "Low",
            "confidence": float (0-1),
            "model_used": "xgboost_cdc_nhamcs",
            "abstain": bool (True if confidence < 0.6),
            "feature_contributions": dict (top 5 importances)
        }
    """
    model, feature_names = _load_triage_model()

    if model is None:
        return {
            "predicted_severity": None,
            "confidence": 0.0,
            "model_used": "unavailable",
            "abstain": True,
            "feature_contributions": {}
        }

    # --- Map patient_data to model feature vector ---
    feature_vector = {}

    # Demographics
    feature_vector['age'] = patient_data.get('age', np.nan)
    gender = patient_data.get('gender', '')
    feature_vector['is_female'] = 1 if gender and gender.lower() == 'female' else 0

    # Vitals mapping (Curago field names -> NHAMCS feature names)
    vitals_map = {
        'temperature': 'tempf',
        'pulse': 'pulse',
        'respiratory_rate': 'respr',
        'bp_systolic': 'bpsys',
        'bp_diastolic': 'bpdias',
        'spo2': 'popct',
    }
    for curago_key, nhamcs_key in vitals_map.items():
        val = patient_data.get(curago_key)
        if nhamcs_key in feature_names:
            feature_vector[nhamcs_key] = float(val) if val is not None else np.nan

    # Pain scale
    if 'pain_scale' in feature_names:
        feature_vector['pain_scale'] = patient_data.get('pain_scale', np.nan)

    # RFV (reason for visit) features — set all to 0 (we don't have NHAMCS codes from voice calls)
    for feat in feature_names:
        if feat.startswith('rfv_') and feat not in feature_vector:
            feature_vector[feat] = 0

    # Build numpy array in correct feature order
    X = np.array([[feature_vector.get(f, np.nan) for f in feature_names]])

    # Predict
    try:
        proba = model.predict_proba(X)[0]  # [P(low), P(high)]
        confidence = float(max(proba))
        predicted_class = int(model.predict(X)[0])
        predicted_severity = "High" if predicted_class == 1 else "Low"

        # Abstain if confidence is too low
        abstain = confidence < 0.60

        # Get feature importances (from the XGBoost model inside the pipeline)
        clf = model.named_steps['clf']
        importances = clf.feature_importances_
        top_indices = np.argsort(importances)[-5:][::-1]
        feature_contributions = {
            feature_names[i]: round(float(importances[i]), 4)
            for i in top_indices
        }

        return {
            "predicted_severity": predicted_severity,
            "confidence": round(confidence, 3),
            "model_used": "xgboost_cdc_nhamcs",
            "abstain": abstain,
            "feature_contributions": feature_contributions
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        return {
            "predicted_severity": None,
            "confidence": 0.0,
            "model_used": "error",
            "abstain": True,
            "feature_contributions": {}
        }


def detect_outbreaks_statistical(tickets_by_village: dict, window_days: int = 7) -> list:
    """
    Detect outbreak anomalies from ticket data.

    Input: {village_name: [list of created_at ISO datetime strings]}
    Output: list of outbreak alert dicts sorted by z_score descending

    Method: For each village, compare current window count vs historical mean.
    Alert if current > mean + 2*std (z-score > 2).
    Uses real per-week std when enough history, falls back to mean*0.5 estimate.
    """
    from datetime import datetime, timedelta

    alerts = []
    now = datetime.utcnow()
    window_start = now - timedelta(days=window_days)

    for village, dates in tickets_by_village.items():
        parsed = []
        for d in dates:
            if isinstance(d, str):
                try:
                    parsed.append(datetime.fromisoformat(d.replace('Z', '')))
                except Exception:
                    continue
            else:
                parsed.append(d)

        if len(parsed) < 3:
            continue

        current_count = sum(1 for d in parsed if d >= window_start)
        min_date = min(parsed)
        total_days = max(1, (now - min_date).days)
        total_weeks = max(1, total_days / 7)
        historical_mean = len(parsed) / total_weeks

        # Real weekly-bin std when >=3 weeks of history, else estimate
        if total_days >= 21:
            week_counts = []
            cursor = min_date
            while cursor < now:
                nxt = cursor + timedelta(days=7)
                week_counts.append(sum(1 for d in parsed if cursor <= d < nxt))
                cursor = nxt
            historical_std = float(np.std(week_counts)) if len(week_counts) > 1 else max(1.0, historical_mean * 0.5)
            historical_std = max(0.5, historical_std)
        else:
            historical_std = max(1.0, historical_mean * 0.5)

        z_score = (current_count - historical_mean) / historical_std

        if z_score > 2.0 and current_count >= 3:
            alerts.append({
                "village": village,
                "current_week_cases": current_count,
                "historical_weekly_avg": round(historical_mean, 1),
                "z_score": round(float(z_score), 2),
                "alert_level": "Critical" if z_score > 3 else "High" if z_score > 2.5 else "Warning",
                "message": f"Anomaly: {current_count} cases in {village} this week vs avg {historical_mean:.1f}/week (z={z_score:.1f})"
            })

    return sorted(alerts, key=lambda x: x['z_score'], reverse=True)


def _load_disease_model():
    global _disease_model
    if _disease_model is None:
        pkl_path = MODEL_DIR / "disease_clf.joblib"
        if pkl_path.exists():
            _disease_model = joblib.load(pkl_path)
            print("Disease classifier loaded")
        else:
            print(f"Disease model not found at {pkl_path}")
    return _disease_model


def predict_disease(text: str) -> dict:
    """
    Symptom-text -> disease (REAL Symptom2Disease model, 24 diseases).
    Returns {label, top3:[{label, prob}], confidence, model_used, data_mode}.
    data_mode reflects DS_DATA_MODE env (informational; model file is fixed).
    """
    model = _load_disease_model()
    mode = data_mode()
    if model is None or not (text or "").strip():
        return {"label": None, "top3": [], "confidence": 0.0,
                "model_used": "unavailable", "data_mode": mode}
    try:
        proba = model.predict_proba([text.strip().lower()])[0]
        classes = list(model.classes_)
        order = np.argsort(proba)[::-1][:3]
        top3 = [{"label": classes[i], "prob": round(float(proba[i]), 3)} for i in order]
        return {"label": top3[0]["label"], "top3": top3,
                "confidence": top3[0]["prob"],
                "model_used": "tfidf-svc_symptom2disease",
                "data_mode": mode}
    except Exception as e:
        print(f"Disease prediction error: {e}")
        return {"label": None, "top3": [], "confidence": 0.0,
                "model_used": "error", "data_mode": mode}
