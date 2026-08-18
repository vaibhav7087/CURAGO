from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.database import supabase

router = APIRouter()

class Vitals(BaseModel):
    bp: Optional[str] = None
    spo2: Optional[int] = None
    temp: Optional[float] = None

@router.get("/tasks/all")
def get_all_tasks():
    """Fetches all home visits commissioned for vitals check."""
    res = supabase.table("tickets").select("*, patients(*)").execute()
    
    tasks = []
    for t in res.data:
        # Either a doctor explicitly assigned a trainee, or the system flagged it for vitals check (needs_vitals)
        if t.get("assigned_trainee_id") is not None or t.get("status") == "needs_vitals":
            tasks.append(t)
            
    return tasks

@router.get("/{trainee_id}/tasks")
def get_trainee_tasks(trainee_id: str):
    """Fetches home visits assigned to this specific intern."""
    res = supabase.table("tickets").select("*, patients(*)").eq("assigned_trainee_id", trainee_id).eq("status", "open").execute()
    return res.data

@router.patch("/{ticket_id}/vitals")
def update_vitals(ticket_id: str, vitals: Vitals):
    """Accepts BP, SpO2, and Temp. Updates the vitals_data JSONB column."""
    res = supabase.table("tickets").update(
        {"vitals_data": vitals.model_dump(exclude_unset=True)}
    ).eq("id", ticket_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "success", "data": res.data[0]}