"""
backend/app/routers/recommend.py
Adaptive prescribing endpoint (v0 brain; full-loop subagent keeps contract).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from ds.recommender import recommend
from app.core.database import supabase

router = APIRouter()


class RecommendRequest(BaseModel):
    symptoms: Optional[str] = None
    symptoms_summary: Optional[str] = None
    disease: Optional[str] = None
    disease_confidence: Optional[float] = None
    age: Optional[int] = None


@router.post("/recommend")
async def recommend_endpoint(req: RecommendRequest):
    """
    Returns formulary-constrained medicine suggestions with why-lines.
    Decision-support only — doctor always overrides.
    """
    try:
        try:
            inv = supabase.table("inventory").select("medicine_name, stock").execute()
            in_stock = [r["medicine_name"] for r in (inv.data or []) if (r.get("stock") or 0) > 0]
        except Exception:
            in_stock = None  # fall back to full formulary
        result = recommend(req.model_dump(), in_stock=in_stock)
        return {"status": "ok", "recommendation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FeedbackRequest(BaseModel):
    ticket_id: str
    choice: str  # accept | edit | reject | manual
    suggested: list = []
    approved: list = []


REWARD = {"accept": 1.0, "edit": 0.5, "reject": 0.0, "manual": 0.0}


@router.post("/rx-feedback")
async def rx_feedback_endpoint(req: FeedbackRequest):
    """
    Logs doctor feedback for the adaptive loop. Non-fatal by design:
    returns ok:false (200) instead of raising so the UI never blocks.
    """
    try:
        sb = supabase.table("rx_feedback").insert({
            "ticket_id": req.ticket_id,
            "suggested": req.suggested,
            "approved": req.approved,
            "reward": REWARD.get(req.choice, 0.0),
        }).execute()
        return {"status": "ok", "id": (sb.data or [{}])[0].get("id")}
    except Exception as e:
        print(f"rx_feedback insert failed (non-fatal): {e}")
        return {"status": "degraded", "detail": "logged locally only"}
