# Curago — Data Science Module

## Datasets Used
- CDC NHAMCS 2019–2022 (public domain, US govt)
- Kaggle Pharma Sales Data (CC-BY-NC 4.0)
- ProMED-mail / IncOVID19 district data

## External Tools Acknowledged
- Groq (LLM inference)
- Vapi (voice AI)
- Supabase (database)
- Google Gemini (embeddings)

## Our Contribution
- Triage severity classifier trained on real CDC data with SHAP explainability
- Outbreak anomaly detection backtested on known Indian outbreaks
- End-to-end voice→triage→doctor→logistics system

## Current Results (regenerate with `py -3.11 train_triage.py`)

| Model | AUC-ROC | Recall | Precision | F1 | Under-triage |
|---|---|---|---|---|---|
| LogReg baseline | 0.932 | 0.858 | 0.605 | 0.709 | 0.142 |
| XGBoost weighted | 0.960 | 0.808 | 0.765 | 0.786 | 0.192 |

Artifacts: `models/triage.pkl`, `models/metric_table.csv`, `models/shap_summary.png`,
`models/demand_forecast_comparison.png`, `models/outbreak_iso.pkl`.
Run: `py -3.11 train_triage.py && py -3.11 train_forecast.py && py -3.11 train_outbreak.py`
