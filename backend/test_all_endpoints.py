import requests
import json
import time

BASE_URL = "http://127.0.0.1:8002/api"

print("Starting FastAPI Integration Tests...")

def test_webhook_end_call():
    print("\n--- Testing POST /api/webhook/end-call ---")
    payload = {
        "call_id": "test_call_999",
        "caller_number": "+919999999999",
        "transcript": "Patient: I have a high fever and headache since yesterday. Assistant: Let me help you with that. Can I know your age? Patient: I am 35.",
        "gathered_data": {
            "patient_name": "Testing User",
            "severity": "High",
            "symptoms": "Fever, Headache",
            "age": 35,
            "gender": "Male",
            "village": "Test Village"
        }
    }
    try:
        response = requests.post(f"{BASE_URL}/webhook/end-call", json=payload)
        print(f"Status: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
            return response.json().get("ticket_id")
        except:
            print(f"Response (Raw): {response.text}")
            return None
    except Exception as e:
        print(f"Failed: {e}")
        return None

def test_rag_search():
    print("\n--- Testing POST /api/rag/search ---")
    payload = {"query": "Fever and cold"}
    try:
        response = requests.post(f"{BASE_URL}/rag/search", json=payload)
        print(f"Status: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response (Raw): {response.text}")
    except Exception as e:
        print(f"Failed: {e}")

def test_get_tickets():
    print("\n--- Testing GET /api/tickets ---")
    try:
        response = requests.get(f"{BASE_URL}/tickets")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Tickets found: {len(data)}")
    except Exception as e:
        print(f"Failed: {e}")

def test_approve_ticket(ticket_id):
    print("\n--- Testing POST /api/approve ---")
    if not ticket_id:
        print("Skipping... No ticket_id provided.")
        return None
        
    payload = {
        "ticket_id": ticket_id,
        "medicines": [{"name": "Paracetamol", "desc": "Fever"}],
        "patient_phone": "+919999999999",
        "patient_name": "Testing User",
        "delivery_address": "Test Village",
        "shift": "Morning"
    }
    try:
        response = requests.post(f"{BASE_URL}/approve", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json().get("order_id")
    except Exception as e:
        print(f"Failed: {e}")
        return None

def test_get_orders():
    print("\n--- Testing GET /api/orders ---")
    try:
        response = requests.get(f"{BASE_URL}/orders")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Orders found: {len(data)}")
    except Exception as e:
        print(f"Failed: {e}")

def test_update_order_status(order_id):
    print("\n--- Testing PATCH /api/orders/{order_id}/status ---")
    if not order_id:
        print("Skipping... No order_id provided.")
        return
        
    payload = {"status": "Delivered"}
    try:
        response = requests.patch(f"{BASE_URL}/orders/{order_id}/status", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    test_rag_search()
    ticket_id = test_webhook_end_call()
    test_get_tickets()
    
    if ticket_id:
        order_id = test_approve_ticket(ticket_id)
        if order_id:
            test_get_orders()
            test_update_order_status(order_id)
    
    print("\nAutomated Tests Completed.")
