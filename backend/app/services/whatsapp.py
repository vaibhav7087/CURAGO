import os
import requests
from dotenv import load_dotenv

load_dotenv()

META_SYSTEM_TOKEN = "EAAhFOnY7zuIBSGJTfZAzQYNlv1gQCZA9sIMs3474JVZCs3T3D9yKmjMrZBJ971NR7SrQgPz0zZAmAk0S8CwwY1tS9RatsxiiaLYhGu5ZAfZAG2rOjKQyms0wCYdNfKIxbJIgZAdTewToZBFnSZAmifQonyasm9HTVZCCWREK9IE8oS0twoBQrC2X0LWUO6i1EBLSwZDZD"
# Placeholder for the sender phone ID, you'll need to update this with your actual Meta Phone ID
META_PHONE_ID = os.getenv("META_PHONE_ID", "1255690297625490")

def send_whatsapp_message(to_phone: str, message_body: str):
    """Sends a free-form WhatsApp message using Meta Graph API."""
    url = f"https://graph.facebook.com/v19.0/{META_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_SYSTEM_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Clean phone number (strip leading '+' for WhatsApp API if needed, though Meta usually accepts it)
    clean_phone = to_phone.replace("+", "")
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_body
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"WhatsApp sent successfully to {to_phone}")
        return True
    except Exception as e:
        print(f"WhatsApp Error: {e}")
        if hasattr(e, 'response') and e.response:
            print("Response:", e.response.text)
        return False
