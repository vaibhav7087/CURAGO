import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def send_sms(to: str, body: str):
    """Sends an SMS using Twilio. NOTIFY_SMS=1 required, else log-only (demo mode)."""
    if os.getenv("NOTIFY_SMS", "0") != "1":
        print(f"[demo] SMS suppressed to {to}: {body[:80]}")
        return False
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not account_sid or not auth_token or not from_number:
        print("❌ Warning: Twilio credentials not fully configured.")
        return False

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to
        )
        print(f"📱 SMS sent to {to}. Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ Twilio SMS Error: {e}")
        return False
