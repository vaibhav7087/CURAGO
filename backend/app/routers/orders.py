from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.database import supabase
from app.services.sms import send_sms
from app.services.whatsapp import send_whatsapp_message

router = APIRouter()

class OrderStatusUpdate(BaseModel):
    status: str

@router.get("/")
def get_orders(status: Optional[str] = None, shift: Optional[str] = None):
    """Fetches delivery orders, optionally filtered by status and shift."""
    query = supabase.table("orders").select("*")
    if status:
        query = query.eq("status", status)
    if shift:
        query = query.eq("shift", shift)
    
    res = query.order("created_at", desc=True).execute()
    return res.data

@router.patch("/{order_id}/status")
def update_order_status(order_id: str, req: OrderStatusUpdate):
    """Updates order status. If Delivered, sends follow-up SMS."""
    res = supabase.table("orders").update({"status": req.status}).eq("id", order_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Order not found")

    updated_order = res.data[0]

    if req.status == "Delivered" or req.status == "Out for Delivery":
        patient_phone = updated_order.get("patient_phone")
        patient_name = updated_order.get("patient_name", "Patient")
        if patient_phone:
            # Twilio SMS
            sms_body = f"Hi {patient_name}, your medicines status is now: {req.status}. If symptoms persist after 3 days, our system will check in with you."
            send_sms(patient_phone, sms_body)
            # WhatsApp Notification
            wa_body = f"📦 *Curago Pharmacy*\nHi {patient_name},\nYour medicine order is now: *{req.status}*.\n\nThank you for trusting Curago."
            send_whatsapp_message(patient_phone, wa_body)

    return {"status": "ok"}
