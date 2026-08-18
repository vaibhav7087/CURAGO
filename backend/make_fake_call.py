import os
import sys
from dotenv import load_dotenv
from twilio.rest import Client

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv(".env")

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

# The number to call (User's number)
to_number = "+919702377010"

client = Client(account_sid, auth_token)

# Using Twilio's Neural TTS to sound exactly like an AI Assistant
twiml_message = """
<Response>
    <Say voice="Polly.Kajal-Neural" language="en-IN">
        Hello. I am the Curago Health AI assistant. 
        I am calling to follow up on your recent checkup. 
        Because your symptoms have not fully resolved, our system has automatically 
        assigned a field trainee to visit your home today to check your vitals. 
        Please stay at your location. We wish you a speedy recovery!
    </Say>
</Response>
"""

import urllib.parse

def make_call():
    print(f"Calling {to_number} from {twilio_number}...")
    try:
        encoded_twiml = urllib.parse.quote(twiml_message.strip())
        url = f"http://twimlets.com/echo?Twiml={encoded_twiml}"
        
        call = client.calls.create(
            url=url,
            to=to_number,
            from_=twilio_number
        )
        print(f"Call initiated successfully! Your phone should be ringing. Call SID: {call.sid}")
    except Exception as e:
        print(f"Failed to initiate call: {e}")

if __name__ == "__main__":
    make_call()
