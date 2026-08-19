from fastapi import APIRouter
from app.core.database import supabase
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/outbreaks")
async def get_outbreaks():
    # 1. Calculate 4-day rolling window for general fetching
    four_days_ago = datetime.utcnow() - timedelta(days=4)
    four_days_ago_str = four_days_ago.isoformat()
    
    # 2. Fetch all tickets mapped to patients to generate comprehensive demo stats
    res = supabase.table("tickets").select("id, status, severity, symptoms_summary, created_at, patients(*)").execute()
    tickets = res.data or []
    
    # 3. Aggregate data
    village_counts = {}
    disease_counts = {"Dengue Fever": 0, "Viral Fever": 0, "Other": 0}
    age_groups = {"0-18": 0, "19-35": 0, "36-50": 0, "51+": 0}
    status_counts = {}
    gender_counts = {"Male": 0, "Female": 0, "Other": 0}
    
    critical_count = 0
    resolved_count = 0
    
    for t in tickets:
        p = t.get("patients") or {}
        village = p.get("village", "Unknown")
        status = t.get("status", "unknown")
        severity = t.get("severity", "Low")
        symptoms = (t.get("symptoms_summary") or "").lower()
        age = p.get("age")
        gender = p.get("gender", "Other")
        
        # Status
        status_counts[status] = status_counts.get(status, 0) + 1
        if status in ["closed"]:
            resolved_count += 1
            
        # Severity
        if severity == "High":
            critical_count += 1
            
        # Village Breakdown
        if village not in village_counts:
            village_counts[village] = {"total": 0, "high": 0, "medium": 0, "low": 0}
        village_counts[village]["total"] += 1
        if severity == "High": village_counts[village]["high"] += 1
        elif severity == "Medium": village_counts[village]["medium"] += 1
        else: village_counts[village]["low"] += 1
            
        # Disease Breakdown (Fake NLP categorization)
        if "fever" in symptoms and ("joint" in symptoms or "rash" in symptoms or "eye" in symptoms or "breakbone" in symptoms or "gum" in symptoms):
            disease_counts["Dengue Fever"] += 1
        elif "fever" in symptoms:
            disease_counts["Viral Fever"] += 1
        else:
            disease_counts["Other"] += 1
            
        # Age Breakdown
        if age is not None:
            if age <= 18: age_groups["0-18"] += 1
            elif age <= 35: age_groups["19-35"] += 1
            elif age <= 50: age_groups["36-50"] += 1
            else: age_groups["51+"] += 1
            
        # Gender Breakdown
        if gender in gender_counts:
            gender_counts[gender] += 1
            
    # 4. Generate Outbreak Alerts (threshold > 2 in same village)
    outbreaks = []
    THRESHOLD = 2
    for village, stats in village_counts.items():
        if stats["total"] >= THRESHOLD:
            outbreaks.append({
                "village": village,
                "case_count": stats["total"],
                "time_window": "4 Days",
                "alert_level": "High" if stats["high"] > 0 else "Medium",
                "message": f"⚠️ Outbreak Warning: {stats['total']} cases reported in {village}."
            })
            
    # Format for JSON
    region_breakdown = [{"region": v, "total_cases": s["total"], "high_severity": s["high"], "medium_severity": s["medium"], "low_severity": s["low"]} for v, s in village_counts.items()]
    disease_breakdown = [{"disease": d, "count": c} for d, c in disease_counts.items()]
    age_breakdown = [{"group": g, "count": c} for g, c in age_groups.items()]
    status_breakdown_list = [{"status": s, "count": c} for s, c in status_counts.items()]
    gender_breakdown_list = [{"gender": g, "count": c} for g, c in gender_counts.items()]
            
    return {
        "outbreaks": outbreaks,
        "region_breakdown": region_breakdown,
        "disease_breakdown": disease_breakdown,
        "age_breakdown": age_breakdown,
        "status_breakdown": status_breakdown_list,
        "gender_breakdown": gender_breakdown_list,
        "total_patients": len(tickets),
        "critical_count": critical_count,
        "resolved_count": resolved_count
    }
