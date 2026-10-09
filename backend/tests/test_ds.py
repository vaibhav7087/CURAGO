"""DS integration tests: triage model, outbreak stats, predict endpoint,
enhanced analytics endpoint, webhook DS merge, and model artifacts.

Hermetic: supabase + LLM calls are mocked. No network.
Run:  py -3.11 -m pytest tests/test_ds.py -v   (from backend/)
"""
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
DS_MODELS = REPO_ROOT / "ds" / "models"


# ---------------------------------------------------------------- unit: ds.predict
class TestPredictSeverityUnit:
    def test_high_for_critical_vitals(self):
        from ds.predict import predict_severity
        r = predict_severity({"age": 55, "gender": "Male", "pulse": 120, "spo2": 85})
        assert r["predicted_severity"] == "High"
        assert r["confidence"] > 0.6
        assert r["abstain"] is False
        assert r["model_used"] == "xgboost_cdc_nhamcs"
        assert len(r["feature_contributions"]) == 5

    def test_low_for_healthy_vitals(self):
        from ds.predict import predict_severity
        r = predict_severity({"age": 25, "gender": "Female", "pulse": 72, "spo2": 99,
                              "temperature": 98.6, "bp_systolic": 115,
                              "bp_diastolic": 75, "pain_scale": 1})
        assert r["predicted_severity"] == "Low"
        assert r["abstain"] is False

    def test_empty_input_abstains_or_returns_shape(self):
        from ds.predict import predict_severity
        r = predict_severity({})
        assert set(r) == {"predicted_severity", "confidence", "model_used",
                          "abstain", "feature_contributions"}
        # empty vitals must not crash; either abstains or predicts Low
        assert r["predicted_severity"] in ("High", "Low", None)

    def test_model_unavailable_path(self):
        import ds.predict as P
        with patch.object(Path, "exists", return_value=False):
            P._triage_model = None
            P._triage_features = None
            r = P.predict_severity({"age": 40})
            assert r["model_used"] == "unavailable"
            assert r["abstain"] is True
            P._triage_model = None  # force reload next test
            P._triage_features = None


class TestOutbreakStatsUnit:
    def _iso_week_dates(self, n_recent=8, n_old=4):
        now = datetime.utcnow()
        recent = [(now - timedelta(days=d)).isoformat() for d in range(n_recent)]
        old = [(now - timedelta(days=30 + d * 7)).isoformat() for d in range(n_old)]
        return recent + old

    def test_spike_triggers_alert_sorted_first(self):
        from ds.predict import detect_outbreaks_statistical
        alerts = detect_outbreaks_statistical({
            "Dharampur": self._iso_week_dates(n_recent=8, n_old=4),
            "Quietville": [(datetime.utcnow() - timedelta(days=40)).isoformat()] * 3,
        })
        assert len(alerts) >= 1
        assert alerts[0]["village"] == "Dharampur"
        assert alerts[0]["z_score"] > 2.0
        assert alerts[0]["alert_level"] in ("Warning", "High", "Critical")

    def test_flat_village_no_alert(self):
        from ds.predict import detect_outbreaks_statistical
        now = datetime.utcnow()
        flat = [(now - timedelta(days=d * 9)).isoformat() for d in range(6)]
        assert detect_outbreaks_statistical({"Flat": flat}) == []

    def test_min_three_tickets_rule(self):
        from ds.predict import detect_outbreaks_statistical
        now = datetime.utcnow()
        two = [(now - timedelta(hours=1)).isoformat(),
               (now - timedelta(hours=2)).isoformat()]
        assert detect_outbreaks_statistical({"Tiny": two}) == []

    def test_bad_dates_skipped_not_crash(self):
        from ds.predict import detect_outbreaks_statistical
        out = detect_outbreaks_statistical({"Messy": ["not-a-date", None, 123]})
        assert out == []


# ---------------------------------------------------------------- endpoint: predict
def _client():
    from app.main import app
    return TestClient(app)


class TestPredictEndpoint:
    def test_valid_critical(self):
        c = _client()
        r = c.post("/api/predict-severity",
                   json={"age": 55, "gender": "Male", "pulse": 120, "spo2": 85})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        pred = body["prediction"]
        assert pred["predicted_severity"] == "High"
        assert pred["abstain"] is False

    def test_empty_body_ok_shape(self):
        c = _client()
        r = c.post("/api/predict-severity", json={})
        assert r.status_code == 200
        assert "prediction" in r.json()

    def test_invalid_type_422(self):
        c = _client()
        r = c.post("/api/predict-severity", json={"age": "not-a-number"})
        assert r.status_code == 422


# ---------------------------------------------------------------- endpoint: enhanced
def _mock_table_router(supabase_mock, tickets, orders):
    """Route supabase.table(name) -> mock whose select().limit().execute()
    returns tickets or orders depending on table name."""
    def table(name):
        m = MagicMock()
        sel = MagicMock()
        m.select.return_value = sel
        lim = MagicMock()
        sel.limit.return_value = lim
        res = MagicMock()
        res.data = tickets if name == "tickets" else orders
        lim.execute.return_value = res
        return m
    supabase_mock.table.side_effect = table


class TestEnhancedAnalytics:
    def test_shape_and_metrics(self):
        from app.routers import analytics as A
        now = datetime.utcnow()
        # 8 recent (spike) + 4 old spread over 60d -> low weekly avg -> z alert.
        # 1 closed ticket 5h ago for the median-resolution assertion.
        tickets = [
            {"id": f"t{i}", "status": "open",
             "severity": "High" if i == 0 else "Low",
             "symptoms_summary": "fever" if i == 0 else "cough",
             "created_at": (now - timedelta(hours=i)).isoformat(),
             "updated_at": (now - timedelta(hours=i)).isoformat(),
             "patients": {"village": "Dharampur"}}
            for i in range(8)
        ] + [
            {"id": f"old{i}", "status": "open", "severity": "Low",
             "symptoms_summary": "cough",
             "created_at": (now - timedelta(days=20 + i * 12)).isoformat(),
             "updated_at": (now - timedelta(days=20 + i * 12)).isoformat(),
             "patients": {"village": "Dharampur"}}
            for i in range(4)
        ] + [
            {"id": "sold", "status": "closed", "severity": "Low",
             "symptoms_summary": "cold",
             "created_at": (now - timedelta(hours=5)).isoformat(),
             "updated_at": now.isoformat(),
             "patients": {"village": "Rampur"}},
        ]
        orders = [
            {"id": "o1", "status": "Delivered", "created_at": now.isoformat()},
            {"id": "o2", "status": "In Transit", "created_at": now.isoformat()},
            {"id": "o3", "status": "Pending", "created_at": now.isoformat()},
        ]
        with patch.object(A, "supabase") as mock_sb:
            _mock_table_router(mock_sb, tickets, orders)
            c = _client()
            r = c.get("/api/analytics/enhanced")
        assert r.status_code == 200
        body = r.json()
        assert set(body) == {"outbreak_alerts", "daily_trend", "order_stats",
                             "median_resolution_hours", "total_tickets"}
        assert len(body["daily_trend"]) == 30
        assert body["order_stats"] == {"pending": 1, "in_transit": 1,
                                       "delivered": 1, "total": 3}
        assert body["median_resolution_hours"] == 5.0
        assert body["total_tickets"] == len(tickets)
        # 8 recent vs ~1.4/wk history -> z alert on Dharampur
        assert any(a["village"] == "Dharampur" for a in body["outbreak_alerts"])

    def test_empty_db_shape(self):
        from app.routers import analytics as A
        with patch.object(A, "supabase") as mock_sb:
            _mock_table_router(mock_sb, [], [])
            c = _client()
            r = c.get("/api/analytics/enhanced")
        assert r.status_code == 200
        body = r.json()
        assert body["outbreak_alerts"] == []
        assert len(body["daily_trend"]) == 30
        assert body["median_resolution_hours"] is None


# ---------------------------------------------------------------- webhook DS merge
class TestWebhookDsMerge:
    def _supabase_mock(self):
        """Full webhook chain: new patient -> new ticket, existing
        extracted_symptoms holds advanced_diagnosis that must survive merge."""
        sb = MagicMock()
        sb._registry = {}

        def table(name):
            if name in sb._registry:
                return sb._registry[name]
            m = MagicMock()
            sb._registry[name] = m
            if name == "patients":
                sel = MagicMock()
                m.select.return_value = sel
                eq = MagicMock()
                sel.eq.return_value = eq
                eq.execute.return_value = MagicMock(data=[])  # new patient
                ins = MagicMock()
                m.insert.return_value = ins
                ins.execute.return_value = MagicMock(data=[{"id": "pat-1"}])
            elif name == "tickets":
                # .select().eq().order().limit().execute -> no recent (proceed)
                # .select().eq().execute -> existing extracted_symptoms
                sel = MagicMock()
                m.select.return_value = sel
                eq = MagicMock()
                sel.eq.return_value = eq
                order = MagicMock()
                eq.order.return_value = order
                lim = MagicMock()
                order.limit.return_value = lim

                # NOTE: dedup check uses order().limit().execute() (stubbed
                # empty below). eq().execute() is only the existing
                # extracted_symptoms fetch -> always returns advanced_diagnosis.
                def _execute(*a, **k):
                    return MagicMock(data=[{"extracted_symptoms":
                                            {"advanced_diagnosis": "Keep me"}}])
                lim.execute.return_value = MagicMock(data=[])  # dedup empty
                eq.execute.side_effect = _execute
                ins = MagicMock()
                m.insert.return_value = ins
                ins.execute.return_value = MagicMock(data=[{"id": "tick-1"}])
                upd = MagicMock()
                m.update.return_value = upd
                eq2 = MagicMock()
                upd.eq.return_value = eq2
                eq2.execute.return_value = MagicMock(data=[])
                m._captured_update = upd
            return m

        sb.table.side_effect = table
        return sb

    def test_ds_prediction_merged_not_overwritten(self):
        from app.routers import webhook as W
        sb = self._supabase_mock()
        fake_ds = {"predicted_severity": "High", "confidence": 0.9,
                   "model_used": "xgboost_cdc_nhamcs", "abstain": False,
                   "feature_contributions": {}}
        with patch.object(W, "supabase", sb), \
             patch.object(W, "extract_patient_data",
                          return_value={"patient_name": "QA Pat",
                                        "severity": "High",
                                        "symptoms": "fever",
                                        "age": 40, "gender": "Male",
                                        "village": "Rampur"}), \
             patch("ds.predict.predict_severity", return_value=fake_ds):
            # webhook imports ds.predict lazily; patch both import sites
            import ds.predict as P
            with patch.object(P, "predict_severity", return_value=fake_ds):
                c = _client()
                r = c.post("/api/webhook/end-call", json={
                    "call_id": "qa-1", "caller_number": "+910000000001",
                    "transcript": "fever", "gathered_data": {}})
        assert r.status_code == 200
        assert r.json()["ticket_id"] == "tick-1"
        # same mock instance serves all tickets calls (registry) -> assert merge
        update_mock = sb._registry["tickets"].update
        assert update_mock.called
        payload = update_mock.call_args[0][0]
        assert payload["extracted_symptoms"]["ds_prediction"] == fake_ds
        assert payload["extracted_symptoms"]["advanced_diagnosis"] == "Keep me"
        assert payload["extracted_symptoms"]["llm_severity"] == "High"


# ---------------------------------------------------------------- artifacts
class TestDsArtifacts:
    def test_triage_pkl_loads_and_features_match(self):
        import joblib
        model = joblib.load(DS_MODELS / "triage.pkl")
        with open(DS_MODELS / "triage_features.json") as f:
            feats = json.load(f)
        assert len(feats) == 29
        assert hasattr(model, "predict_proba")

    def test_metric_table_two_rows(self):
        import pandas as pd
        df = pd.read_csv(DS_MODELS / "metric_table.csv")
        assert len(df) == 2
        assert set(df["Model"]) == {"Logistic Regression (baseline)",
                                    "XGBoost (class-weighted)"}
        assert (df["AUC-ROC"] > 0.8).all()

    def test_images_and_forecast_exist(self):
        import pandas as pd
        assert (DS_MODELS / "shap_summary.png").stat().st_size > 10_000
        assert (DS_MODELS / "demand_forecast_comparison.png").stat().st_size > 10_000
        fdf = pd.read_csv(DS_MODELS / "demand_forecast_metrics.csv")
        assert len(fdf) == 8
        assert (DS_MODELS / "outbreak_iso.pkl").exists()

# ---------------------------------------------------------------- disease + recommend
class TestDiseaseAndRecommend:
    def test_predict_disease_unit(self):
        from ds.predict import predict_disease
        r = predict_disease("fever with body ache and chills for three days")
        assert r["label"] in json.load(open(DS_MODELS / "disease_labels.json"))["labels"]
        assert len(r["top3"]) == 3
        assert r["confidence"] > 0
        assert r["model_used"] == "tfidf-svc_symptom2disease"
        assert r["data_mode"] in ("real", "synthetic")

    def test_predict_disease_empty(self):
        from ds.predict import predict_disease
        r = predict_disease("   ")
        assert r["label"] is None
        assert r["top3"] == []

    def test_disease_endpoint(self):
        c = _client()
        r = c.post("/api/predict-disease", json={"text": "red itchy skin rash with scaly patches"})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["prediction"]["label"] is not None

    def _mock_inventory(self, mock_sb, rows):
        m = MagicMock()
        sel = MagicMock()
        m.select.return_value = sel
        res = MagicMock()
        res.data = rows
        sel.execute.return_value = res
        mock_sb.table.return_value = m

    def test_recommend_endpoint_v0(self):
        from app.routers import recommend as R
        inv = [{"medicine_name": m, "stock": 10} for m in
               ["Paracetamol 500mg", "Amoxicillin 250mg", "Ibuprofen 400mg",
                "Ceftriaxone Inj 1g", "ORS Packets"]]
        with patch.object(R, "supabase") as mock_sb:
            self._mock_inventory(mock_sb, inv)
            c = _client()
            r = c.post("/api/recommend", json={"symptoms": "high fever and chills for three days"})
        assert r.status_code == 200
        rec = r.json()["recommendation"]
        assert rec["abstain"] is False
        assert rec["model"] in ("v0-rules", "bandit-v1", "rules-fallback")
        assert len(rec["suggestions"]) > 0
        assert all(s["in_stock"] for s in rec["suggestions"])
        assert all("why" in s and "dose" in s for s in rec["suggestions"])

    def test_recommend_respects_stock(self):
        from app.routers import recommend as R
        inv = [{"medicine_name": "ORS Packets", "stock": 50}]
        with patch.object(R, "supabase") as mock_sb:
            self._mock_inventory(mock_sb, inv)
            c = _client()
            r = c.post("/api/recommend", json={"symptoms": "high fever and chills for three days"})
        rec = r.json()["recommendation"]
        names = [s["medicine"] for s in rec["suggestions"]]
        assert names and all(n == "ORS Packets" for n in names)

    def test_recommend_abstains_on_gibberish(self):
        from app.routers import recommend as R
        inv = [{"medicine_name": "Paracetamol 500mg", "stock": 10}]
        with patch.object(R, "supabase") as mock_sb:
            self._mock_inventory(mock_sb, inv)
            c = _client()
            r = c.post("/api/recommend", json={"symptoms": "xyzzy qqq frobnicator"})
        rec = r.json()["recommendation"]
        assert rec["abstain"] is True
        assert rec["suggestions"] == []

    def test_bandit_reorder_safe_on_priors(self):
        from ds.recommender import recommend
        r = recommend({"symptoms": "fever and body ache"}, in_stock=["Paracetamol 500mg", "ORS Packets"])
        assert r["model"] in ("v0-rules", "rules-fallback")  # priors-only weights -> no learned reorder
        assert [s["medicine"] for s in r["suggestions"]] == ["Paracetamol 500mg", "ORS Packets"]

    def test_disease_artifacts(self):
        import pandas as pd
        df = pd.read_csv(DS_MODELS / "disease_metrics.csv")
        assert len(df) == 2
        assert (df["F1-macro"] > 0.8).all()
        assert "real" in df["Data Source"].iloc[0]
        assert (DS_MODELS / "disease_confusion.png").stat().st_size > 10_000
        assert (DS_MODELS / "disease_clf.joblib").exists()

class TestRxFeedback:
    def test_insert_ok(self):
        from app.routers import recommend as R
        m = MagicMock()
        ins = MagicMock()
        m.insert.return_value = ins
        ins.execute.return_value = MagicMock(data=[{"id": "fb-1"}])
        with patch.object(R, "supabase") as mock_sb:
            mock_sb.table.return_value = m
            c = _client()
            r = c.post("/api/rx-feedback", json={"ticket_id": "t1", "choice": "accept",
                                                 "suggested": ["Paracetamol 500mg"],
                                                 "approved": ["Paracetamol 500mg"]})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["id"] == "fb-1"
        payload = m.insert.call_args[0][0]
        assert payload["reward"] == 1.0

    def test_reward_mapping_edit(self):
        from app.routers import recommend as R
        m = MagicMock()
        ins = MagicMock()
        m.insert.return_value = ins
        ins.execute.return_value = MagicMock(data=[{"id": "fb-2"}])
        with patch.object(R, "supabase") as mock_sb:
            mock_sb.table.return_value = m
            c = _client()
            c.post("/api/rx-feedback", json={"ticket_id": "t1", "choice": "edit",
                                             "suggested": ["A", "B"], "approved": ["A"]})
        assert m.insert.call_args[0][0]["reward"] == 0.5

    def test_db_down_degraded_not_500(self):
        from app.routers import recommend as R
        with patch.object(R, "supabase") as mock_sb:
            mock_sb.table.side_effect = Exception("db down")
            c = _client()
            r = c.post("/api/rx-feedback", json={"ticket_id": "t1", "choice": "reject",
                                                 "suggested": ["A"], "approved": []})
        assert r.status_code == 200
        assert r.json()["status"] == "degraded"
