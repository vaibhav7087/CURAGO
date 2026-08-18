import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

# --- 1. Test Analytics Endpoint ---
@patch("app.routers.analytics.supabase")
def test_analytics_outbreaks(mock_supabase):
    # Mock supabase response to simulate an outbreak in 'Dharampur'
    mock_execute = MagicMock()
    mock_execute.data = [
        {"id": "1", "symptoms_summary": "Fever", "patients": {"village": "Dharampur"}},
        {"id": "2", "symptoms_summary": "Cough", "patients": {"village": "Dharampur"}},
        {"id": "3", "symptoms_summary": "Fever and chills", "patients": {"village": "Dharampur"}},
        {"id": "4", "symptoms_summary": "Headache", "patients": {"village": "Rampur"}},
    ]
    mock_supabase.table().select().gte().execute.return_value = mock_execute

    response = client.get("/api/analytics/outbreaks")
    assert response.status_code == 200
    data = response.json()
    assert "outbreaks" in data
    
    # Threshold is 3, so Dharampur should trigger an outbreak, Rampur should not.
    outbreaks = data["outbreaks"]
    assert len(outbreaks) == 1
    assert outbreaks[0]["village"] == "Dharampur"
    assert outbreaks[0]["case_count"] == 3
    assert "4-Day Outbreak Warning" in outbreaks[0]["message"]

# --- 2. Test Vitals Endpoint (Interactive AI) ---
@patch("app.routers.vitals.supabase")
@patch("app.routers.vitals.groq_client")
def test_submit_vitals_needs_more_checks(mock_groq, mock_supabase):
    # Mock DB fetching ticket
    mock_ticket_res = MagicMock()
    mock_ticket_res.data = [{"id": "ticket123", "symptoms_summary": "Chest pain", "vitals_data": {}}]
    mock_supabase.table().select().eq().execute.return_value = mock_ticket_res
    
    # Mock Groq LLM returning "needs_more_checks"
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [
        MagicMock(message=MagicMock(content='{"status": "needs_more_checks", "requested_checks": ["Check ECG"] }'))
    ]
    mock_groq.chat.completions.create.return_value = mock_llm_response
    
    payload = {
        "temperature": "98.6",
        "blood_pressure": "140/90",
        "spo2": "95"
    }
    
    response = client.post("/api/tickets/vitals/ticket123", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_checks"
    assert "Check ECG" in data["requested_checks"]

@patch("app.routers.vitals.supabase")
@patch("app.routers.vitals.groq_client")
def test_submit_vitals_complete(mock_groq, mock_supabase):
    # Mock DB fetching ticket
    mock_ticket_res = MagicMock()
    mock_ticket_res.data = [{"id": "ticket123", "symptoms_summary": "Chest pain", "vitals_data": {}}]
    mock_supabase.table().select().eq().execute.return_value = mock_ticket_res
    
    # Mock Groq LLM returning "complete"
    mock_llm_response = MagicMock()
    mock_llm_response.choices = [
        MagicMock(message=MagicMock(content='{"status": "complete", "advanced_diagnosis": "Mild Hypertension." }'))
    ]
    mock_groq.chat.completions.create.return_value = mock_llm_response
    
    payload = {
        "temperature": "98.6",
        "blood_pressure": "120/80",
        "spo2": "99"
    }
    
    response = client.post("/api/tickets/vitals/ticket123", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert data["advanced_diagnosis"] == "Mild Hypertension."

# --- 3. Test Orders Endpoint (WhatsApp Integration) ---
@patch("app.routers.orders.supabase")
@patch("app.routers.orders.send_sms")
@patch("app.routers.orders.send_whatsapp_message")
def test_update_order_status_triggers_whatsapp(mock_wa, mock_sms, mock_supabase):
    # Mock DB returning an order with a phone number
    mock_order_res = MagicMock()
    mock_order_res.data = [{"id": "order123", "status": "Out for Delivery", "patient_phone": "919876543210", "patient_name": "Test Patient"}]
    mock_supabase.table().update().eq().execute.return_value = mock_order_res
    
    payload = {"status": "Out for Delivery"}
    response = client.patch("/api/orders/order123/status", json=payload)
    
    assert response.status_code == 200
    # Ensure WhatsApp function was called exactly once with the patient's phone and a formatted message
    mock_wa.assert_called_once()
    args, kwargs = mock_wa.call_args
    assert args[0] == "919876543210"
    assert "Out for Delivery" in args[1]
