import requests
import sys

def simulate_sms(phone_number, message_body):
    url = "https://curago-backend.onrender.com/api/webhook/twilio-sms"
    
    # Twilio sends data as form-urlencoded
    payload = {
        "From": phone_number,
        "Body": message_body
    }
    
    print(f"Simulating incoming SMS from {phone_number}...")
    print(f"Message: '{message_body}'\n")
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Webhook hit successfully! The backend is processing the SMS.")
        else:
            print(f"❌ Failed to hit webhook. Status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("--- Twilio SMS Simulator ---")
    phone = input("Enter patient phone number (e.g., +919998887777): ")
    message = input("Enter SMS reply (e.g., 'I am still sick'): ")
    
    simulate_sms(phone, message)
