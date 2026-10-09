from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.core.database import supabase

router = APIRouter()

# Canonical trainee used by the demo. The frontend may send friendly aliases.
CANONICAL_TRAINEE_ID = "11111111-1111-1111-1111-111111111111"
FRIENDLY_IDS = {
    "trainee_001": CANONICAL_TRAINEE_ID,
    "trainee-001": CANONICAL_TRAINEE_ID,
    "default": CANONICAL_TRAINEE_ID,
}


def resolve_trainee_id(raw: str) -> str:
    """Map friendly ids to the canonical UUID and validate the result."""
    resolved = FRIENDLY_IDS.get(raw, raw)
    try:
        UUID(resolved)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid trainee id: {raw!r}")
    return resolved


@router.get("/tasks/all")
def get_all_tasks():
    """Fetches all home visits commissioned for vitals check."""
    res = supabase.table("tickets").select("*, patients(*)").execute()

    tasks = []
    for t in res.data:
        # Only show tickets that actually need vitals collected
        if t.get("status") == "needs_vitals":
            tasks.append(t)

    return tasks


@router.get("/{trainee_id}/tasks")
def get_trainee_tasks(trainee_id: str):
    """Fetches home visits assigned to this specific intern."""
    resolved = resolve_trainee_id(trainee_id)
    res = (
        supabase.table("tickets")
        .select("*, patients(*)")
        .eq("assigned_trainee_id", resolved)
        .eq("status", "open")
        .execute()
    )
    return res.data


@router.patch("/{ticket_id}/vitals")
def update_vitals(ticket_id: str, vitals: dict):
    """Accepts BP, Spo2, Temp, HR etc. Updates the vitals_data JSONB column."""
    clean = {k: v for k, v in vitals.items() if v not in (None, "")}
    if not clean:
        raise HTTPException(status_code=422, detail="No vitals provided")

    res = supabase.table("tickets").update(
        {"vitals_data": clean}
    ).eq("id", ticket_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "success", "data": res.data[0]}
