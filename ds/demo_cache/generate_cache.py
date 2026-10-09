"""
Pre-generate demo data so dashboard works without live Supabase.
Run once: python ds/demo_cache/generate_cache.py
Output: ds/demo_cache/*.json files
"""
import json
import os

os.makedirs(os.path.dirname(__file__) or '.', exist_ok=True)

# --- Pre-computed analytics response ---
demo_analytics = {
    "outbreak_alerts": [
        {
            "village": "Dharampur",
            "current_week_cases": 8,
            "historical_weekly_avg": 2.3,
            "z_score": 4.96,
            "alert_level": "Critical",
            "message": "Anomaly: 8 cases in Dharampur this week vs avg 2.3/week (z=5.0)"
        },
        {
            "village": "Rampur",
            "current_week_cases": 5,
            "historical_weekly_avg": 1.8,
            "z_score": 3.56,
            "alert_level": "High",
            "message": "Anomaly: 5 cases in Rampur this week vs avg 1.8/week (z=3.6)"
        }
    ],
    "daily_trend": [
        {"date": f"2026-09-{str(d).zfill(2)}", "count": c}
        for d, c in zip(range(6, 20), [2, 1, 3, 0, 4, 5, 2, 1, 8, 3, 6, 4, 2, 7])
    ],
    "order_stats": {"pending": 3, "in_transit": 5, "delivered": 18, "total": 26},
    "median_resolution_hours": 4.2,
    "total_tickets": 47
}

with open(os.path.join(os.path.dirname(__file__), "enhanced_analytics.json"), "w") as f:
    json.dump(demo_analytics, f, indent=2)

# --- Demo severity predictions ---
demo_predictions = [
    {"patient": "Rajesh Kumar", "age": 45, "prediction": {"predicted_severity": "High", "confidence": 0.87, "abstain": False, "model_used": "xgboost_cdc_nhamcs"}},
    {"patient": "Anita Sharma", "age": 32, "prediction": {"predicted_severity": "Low", "confidence": 0.73, "abstain": False, "model_used": "xgboost_cdc_nhamcs"}},
    {"patient": "Pooja Verma", "age": 12, "prediction": {"predicted_severity": "High", "confidence": 0.91, "abstain": False, "model_used": "xgboost_cdc_nhamcs"}},
]

with open(os.path.join(os.path.dirname(__file__), "demo_predictions.json"), "w") as f:
    json.dump(demo_predictions, f, indent=2)

print("Demo cache generated!")
