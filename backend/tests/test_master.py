import pytest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_PHONE_NUMBER = "+19998887777"
TEST_PATIENT_NAME = "Automated Test Patient"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_vapi_end_call_webhook_real_api():
    payload = {
        "message": {
            "type": "end-of-call-report",
            "artifact": {
                "transcript": "Hello, I am calling because I have had a severe headache and fever for the last 3 days. My name is Automated Test Patient."
            },
            "call": {
                "customer": {
                    "number": TEST_PHONE_NUMBER
                }
            }
        }
    }
    
    response = client.post("/api/webhook/end-call", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ticket_id" in data


def test_vapi_tool_patient_history_real_api():
    time.sleep(1)
    
    payload = {
        "message": {
            "type": "tool-calls",
            "toolWithToolCallList": [
                {
                    "toolCall": {
                        "id": "call_123",
                        "function": {
                            "name": "get_patient_history",
                            "arguments": {}
                        }
                    }
                }
            ],
            "call": {
                "customer": {
                    "number": TEST_PHONE_NUMBER
                }
            }
        }
    }
    
    response = client.post("/api/vapi-tool", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    result_text = data["results"][0]["result"].lower()
    
    assert "headache" in result_text or "fever" in result_text


def test_twilio_sms_webhook_real_api():
    form_data = {
        "From": TEST_PHONE_NUMBER,
        "Body": "NO, I am still feeling sick."
    }
    
    response = client.post(
        "/api/webhook/twilio-sms",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    
    assert "<?xml" in response.text
    assert "<Response>" in response.text


def test_analytics_outbreaks_endpoint():
    response = client.get("/api/analytics/outbreaks")
    assert response.status_code == 200
    assert "outbreaks" in response.json()
