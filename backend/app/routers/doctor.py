from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.services.sms import send_sms

router = APIRouter()

class ApproveRequest(BaseModel):
    ticket_id: str
    medicines: List[Dict[str, Any]]
    patient_phone: str
    patient_name: str
    delivery_address: str
    shift: str

class EscalateRequest(BaseModel):
    ticket_id: str
    camp_id: str

@router.get("/tickets")
def get_tickets():
    """Fetches all tickets with joined patient data."""
    res = supabase.table("tickets").select("*, patients(*)").execute()
    return res.data

@router.post("/approve")
def approve_ticket(req: ApproveRequest):
    """Resolves ticket, creates order, and sends SMS."""
    # 1. Update ticket
    res_ticket = supabase.table("tickets").update({"status": "resolved"}).eq("id", req.ticket_id).execute()
    if not res_ticket.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # 2. Create order
    order_data = {
        "ticket_id": req.ticket_id,
        "patient_phone": req.patient_phone,
        "patient_name": req.patient_name,
        "package_items": req.medicines,
        "delivery_address": req.delivery_address,
        "shift": req.shift,
        "status": "Pending"
    }
    res_order = supabase.table("orders").insert(order_data).execute()
    order_id = res_order.data[0]['id']

    # 3. Send SMS
    meds_list = ", ".join([m.get("name", "Medicine") for m in req.medicines])
    sms_body = f"Your prescription has been approved. Medicines: {meds_list}. Delivery scheduled for {req.shift} slot."
    sms_sent = send_sms(req.patient_phone, sms_body)

    return {"status": "ok", "order_id": order_id, "sms_sent": sms_sent}

@router.get("/inventory")
def get_inventory():
    """Fetches inventory."""
    res = supabase.table("inventory").select("*").execute()
    return res.data

@router.get("/camps")
def get_camps():
    """Fetches available specialist camps."""
    res = supabase.table("camps").select("*").execute()
    return res.data

@router.post("/escalate")
def escalate_ticket(req: EscalateRequest):
    """Escalates a ticket to a specialist camp."""
    res_ticket = supabase.table("tickets").update({
        "status": "escalated",
        "camp_id": req.camp_id
    }).eq("id", req.ticket_id).execute()

    if not res_ticket.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Increment booked count safely via RPC (if defined) or simple update (hackathon style)
    camp = supabase.table("camps").select("booked_count").eq("id", req.camp_id).execute()
    if camp.data:
        current_count = camp.data[0].get("booked_count", 0)
        supabase.table("camps").update({"booked_count": current_count + 1}).eq("id", req.camp_id).execute()

    return {"status": "ok"}