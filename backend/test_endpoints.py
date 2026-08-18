import requests
import json
import urllib.parse

BASE_URL = "http://127.0.0.1:8000/api"

print("--- Testing Vapi Tool: get_patient_history ---")
vapi_payload = {
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
                "number": "+919702377010"
            }
        }
    }
}
r1 = requests.post(f"{BASE_URL}/vapi-tool", json=vapi_payload)
print("Vapi Tool Response:", r1.status_code)
print(r1.text)


print("\n--- Testing SMS Webhook (NO) ---")
sms_data = {
    "From": "+919702377010",
    "Body": "No, I am still feeling dizzy and sick"
}
r2 = requests.post(f"{BASE_URL}/webhook/twilio-sms", data=sms_data)
print("SMS Webhook Response:", r2.status_code)
print(r2.text)

print("\n--- Testing SMS Webhook (YES) ---")
sms_data_yes = {
    "From": "+919702377010",
    "Body": "Yes I am fully recovered thank you"
}
r3 = requests.post(f"{BASE_URL}/webhook/twilio-sms", data=sms_data_yes)
print("SMS Webhook Response:", r3.status_code)
print(r3.text)

