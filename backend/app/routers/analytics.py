from fastapi import APIRouter
from app.core.database import supabase
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/outbreaks")
async def get_outbreaks():
    # 1. Calculate 4-day rolling window
    four_days_ago = datetime.utcnow() - timedelta(days=4)
    four_days_ago_str = four_days_ago.isoformat()
    
    # 2. Fetch recent tickets mapped to patients (village)
    # Supabase allows joining tables in select.
    res = supabase.table("tickets").select("id, symptoms_summary, created_at, patients(village)").gte("created_at", four_days_ago_str).execute()
    tickets = res.data or []
    
    # 3. Group by village
    village_counts = {}
    for t in tickets:
        p = t.get("patients") or {}
        village = p.get("village")
        if not village:
            continue
            
        symptoms = t.get("symptoms_summary", "")
        if village not in village_counts:
            village_counts[village] = []
        village_counts[village].append(symptoms)
        
    # 4. Analyze for spikes
    outbreaks = []
    THRESHOLD = 3 # More than 3 cases in 4 days triggers an alert
    for village, cases in village_counts.items():
        if len(cases) >= THRESHOLD:
            # We can do advanced NLP fuzzy matching on cases here, but for now we aggregate them
            outbreaks.append({
                "village": village,
                "case_count": len(cases),
                "time_window": "4 Days",
                "alert_level": "High",
                "message": f"⚠️ 4-Day Outbreak Warning: {len(cases)} cases reported in {village}."
            })
            
    return {"outbreaks": outbreaks}
