from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response
import os
import random
import traceback
from pydantic import BaseModel
from app.core.database import supabase
from twilio.rest import Client

router = APIRouter()

# Setup Twilio
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

class FollowupRequest(BaseModel):
    phone_number: str
    ticket_id: str

@router.post("/doctor/send-sms-followup")
async def send_sms_followup(req: FollowupRequest):
    """Called by Doctor Dashboard to manually trigger an SMS follow-up."""
    if not client:
        raise HTTPException(status_code=500, detail="Twilio credentials not configured")
        
    try:
        message = client.messages.create(
            body="Curago Health: Are you feeling better? Reply YES or NO. Or call our AI Helpline and press 3.",
            from_=TWILIO_PHONE_NUMBER,
            to=req.phone_number
        )
        return {"status": "success", "message_sid": message.sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/twilio-sms")
async def twilio_sms_webhook(request: Request):
    """Handles incoming SMS replies from patients."""
    try:
        # Twilio sends data as form-urlencoded
        form_data = await request.form()
        from_number = form_data.get("From")
        body = form_data.get("Body", "").strip().lower()
        
        if not from_number:
            return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")
            
        print(f"Received SMS from {from_number}: {body}")
        
        # If they reply with "no" or "not", we auto-assign a trainee
        if "no" in body or "not" in body:
            print("Patient is not feeling better. Assigning trainee...")
            
            # 1. Fetch patient
            patient_res = supabase.table("patients").select("id").eq("phone_number", from_number).execute()
            if not patient_res.data:
                print("Patient not found in DB.")
                return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")
                
            patient_id = patient_res.data[0]["id"]
            
            # 2. Fetch their open ticket
            ticket_res = supabase.table("tickets").select("id").eq("patient_id", patient_id).in_("status", ["open", "follow_up"]).order("created_at", desc=True).limit(1).execute()
            
            if not ticket_res.data:
                print("No open ticket found for patient.")
                return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")
                
            ticket_id = ticket_res.data[0]["id"]
            
            # 3. Assign a random trainee (Hardcoded fallback since trainees table doesn't exist in this DB)
            assigned_trainee_id = "11111111-1111-1111-1111-111111111111"
            
            # 4. Update ticket
            supabase.table("tickets").update({
                "status": "needs_vitals",
                "assigned_trainee_id": assigned_trainee_id
            }).eq("id", ticket_id).execute()
            
            print(f"Ticket {ticket_id} updated: Needs Vitals, assigned to {assigned_trainee_id}")
            
            # 5. Send confirmation reply
            try:
                client.messages.create(
                    body="We have noted your symptoms. A field trainee has been automatically assigned to visit your home today to check your vitals.",
                    from_=TWILIO_PHONE_NUMBER,
                    to=from_number
                )
            except Exception as e:
                print(f"Twilio send warning: {e}")
            
        elif "yes" in body:
            print("Patient is feeling better.")
            # Send confirmation reply
            try:
                client.messages.create(
                    body="We are glad to hear you are feeling better! We will close your ticket. Stay healthy!",
                    from_=TWILIO_PHONE_NUMBER,
                    to=from_number
                )
            except Exception as e:
                print(f"Twilio send warning: {e}")
                
            # Fetch patient and close ticket
            patient_res = supabase.table("patients").select("id").eq("phone_number", from_number).execute()
            if patient_res.data:
                patient_id = patient_res.data[0]["id"]
                supabase.table("tickets").update({"status": "resolved"}).eq("patient_id", patient_id).in_("status", ["open", "follow_up"]).execute()

        # Respond with empty TwiML (Required by Twilio webhook)
        return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")
        
    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"SMS Webhook Error: {e}\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=str(e))
