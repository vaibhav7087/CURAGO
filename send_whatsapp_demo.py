import requests
import json
import sys

# SECURE LOCAL SCRIPT: These credentials remain ONLY on your machine.
# They are never committed to GitHub or sent to Render.
META_TOKEN = "EAAhFOnY7zuIBSGJTfZAzQYNlv1gQCZA9sIMs3474JVZCs3T3D9yKmjMrZBJ971NR7SrQgPz0zZAmAk0S8CwwY1tS9RatsxiiaLYhGu5ZAfZAG2rOjKQyms0wCYdNfKIxbJIgZAdTewToZBFnSZAmifQonyasm9HTVZCCWREK9IE8oS0twoBQrC2X0LWUO6i1EBLSwZDZD"
PHONE_NUMBER_ID = "1255690297625490"

def send_whatsapp_message(to_number, message_text):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Clean the phone number (remove +, spaces, etc)
    clean_number = "".join(filter(str.isdigit, to_number))
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text
        }
    }
    
    print(f"\n📡 Firing WhatsApp Message via Meta Official API to {clean_number}...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ SUCCESS! Message sent to patient's WhatsApp.")
    else:
        print(f"❌ FAILED to send message. HTTP {response.status_code}")
        print("Error Details:", response.json())
        print("\n💡 NOTE: If you get a 'message failed to send' error, you must text the Meta Test Number first from your WhatsApp to open the 24-hour free-form message window!")

if __name__ == "__main__":
    print("--- WhatsApp Dispatch & Reply Demo (Local Meta API) ---")
    phone = input("Enter patient phone number (e.g., +919702377010): ")
    prescription = input("Enter the prescription/message to send: ")
    
    full_message = f"🏥 Curago Health Alert:\n\nYour prescription has been approved by the doctor.\n\nRx: {prescription}\n\n*If you still feel sick after taking this, please reply to this message with 'I am still sick'.*"
    
    # 1. Send the real WhatsApp message to the phone
    send_whatsapp_message(phone, full_message)
    
    print("\n" + "="*50)
    print("⏳ Waiting for patient to reply on their phone...")
    print("="*50)
    
    while True:
        # 2. Wait for the presenter to type what the patient replied
        reply_text = input("\n[Simulation] Type the patient's reply here (or 'exit' to quit): ")
        if reply_text.strip().lower() == 'exit':
            break
            
        print("🚀 Simulating incoming webhook to Render backend...")
        
        # 3. Fire the simulated webhook to the Render backend!
        # We use the existing Twilio webhook endpoint to process it since it already has the AI logic.
        backend_url = "https://curago-backend.onrender.com/api/webhook/twilio-sms"
        
        # Format phone number for Twilio endpoint expectation
        twilio_phone = phone if phone.startswith("whatsapp:") else f"whatsapp:{phone}"
        if not twilio_phone.startswith("whatsapp:+"):
            twilio_phone = twilio_phone.replace("whatsapp:", "whatsapp:+")
            
        payload = {
            "From": twilio_phone,
            "Body": reply_text
        }
        
        try:
            response = requests.post(backend_url, data=payload)
            if response.status_code == 200:
                print("✅ Backend received the reply and processed the follow-up!")
                print("Check your Netlify Dashboard (refresh if necessary) to see the ticket update!")
            else:
                print(f"❌ Backend returned error: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Failed to reach backend: {e}")
