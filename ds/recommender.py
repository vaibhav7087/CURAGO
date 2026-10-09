"""
ds/recommender.py — v0 adaptive prescribing brain (rules + formulary filter + why-line).
Contract (shared with full-loop subagent — DO NOT change keys):
  recommend(ticket) -> {
    "suggestions": [{"medicine": str, "dose": str, "why": str, "in_stock": bool}],
    "disease": str|None, "confidence": float,
    "model": "v0-rules", "abstain": bool
  }
ticket keys: symptoms (str), disease (optional precomputed), age, vitals dict.
 formulary = in-stock inventory medicine names (passed in or fetched lazily).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ds.predict import predict_disease

# Curated disease -> formulary meds (L1/L2 stock). Conservative: fever/pain first.
FORMULARY_DOSE = {
    "Paracetamol 500mg": "500mg twice daily after food (max 3 days)",
    "Amoxicillin 250mg": "250mg three times daily for 5 days (if no allergy)",
    "Ibuprofen 400mg": "400mg twice daily after food (avoid if ulcer)",
    "Ceftriaxone Inj 1g": "1g IV once daily — L2 depot, trainee supervised",
    "ORS Packets": "1 packet per litre, after every loose stool",
}

DISEASE_MEDS = {
    "Common Cold": ["Paracetamol 500mg", "ORS Packets"],
    "Chicken pox": ["Paracetamol 500mg", "ORS Packets"],
    "Dengue": ["Paracetamol 500mg", "ORS Packets"],
    "Typhoid": ["Paracetamol 500mg", "Amoxicillin 250mg", "ORS Packets"],
    "Malaria": ["Paracetamol 500mg", "ORS Packets"],
    "Pneumonia": ["Paracetamol 500mg", "Amoxicillin 250mg"],
    "Bronchial Asthma": ["Paracetamol 500mg"],
    "Migraine": ["Paracetamol 500mg", "Ibuprofen 400mg"],
    "Arthritis": ["Ibuprofen 400mg", "Paracetamol 500mg"],
    "Cervical spondylosis": ["Ibuprofen 400mg", "Paracetamol 500mg"],
    "Hypertension": ["Paracetamol 500mg"],
    "diabetes": ["Paracetamol 500mg", "ORS Packets"],
    "Jaundice": ["ORS Packets", "Paracetamol 500mg"],
    "peptic ulcer disease": ["Paracetamol 500mg", "ORS Packets"],
    "gastroesophageal reflux disease": ["Paracetamol 500mg"],
    "urinary tract infection": ["Amoxicillin 250mg", "ORS Packets"],
    "drug reaction": ["Paracetamol 500mg", "ORS Packets"],
    "allergy": ["Paracetamol 500mg"],
    "Fungal infection": ["Paracetamol 500mg"],
    "Impetigo": ["Amoxicillin 250mg", "Paracetamol 500mg"],
    "Psoriasis": ["Paracetamol 500mg"],
    "Acne": ["Paracetamol 500mg"],
    "Varicose Veins": ["Ibuprofen 400mg", "Paracetamol 500mg"],
    "Dimorphic Hemorrhoids": ["Ibuprofen 400mg", "ORS Packets"],
}


KEYWORD_MEDS = {
    "fever": ["Paracetamol 500mg", "ORS Packets"],
    "bukhar": ["Paracetamol 500mg", "ORS Packets"],
    "chill": ["Paracetamol 500mg", "ORS Packets"],
    "cough": ["Paracetamol 500mg"],
    "khansi": ["Paracetamol 500mg"],
    "cold": ["Paracetamol 500mg"],
    "pain": ["Ibuprofen 400mg", "Paracetamol 500mg"],
    "ache": ["Ibuprofen 400mg", "Paracetamol 500mg"],
    "dard": ["Ibuprofen 400mg", "Paracetamol 500mg"],
    "headache": ["Paracetamol 500mg", "Ibuprofen 400mg"],
    "rash": ["Paracetamol 500mg"],
    "skin": ["Paracetamol 500mg"],
    "diarrhea": ["ORS Packets"],
    "diarrhoea": ["ORS Packets"],
    "loose": ["ORS Packets"],
    "vomit": ["ORS Packets"],
    "ulcer": ["Paracetamol 500mg", "ORS Packets"],
}


def _formulary(in_stock=None):
    """in_stock: list of medicine names with stock>0. Defaults to full formulary."""
    if in_stock:
        return [m for m in FORMULARY_DOSE if m in set(in_stock)]
    return list(FORMULARY_DOSE)


def recommend(ticket: dict, in_stock=None) -> dict:
    symptoms = str(ticket.get("symptoms") or ticket.get("symptoms_summary") or "")
    disease = ticket.get("disease")
    conf = 0.0
    if not disease and symptoms.strip():
        pred = predict_disease(symptoms)
        disease, conf = pred["label"], pred["confidence"]
    else:
        conf = float(ticket.get("disease_confidence") or 0.0)

    formulary = _formulary(in_stock)
    mapped = DISEASE_MEDS.get(disease or "", [])
    # Formulary filter: only in-stock meds, preserve mapping order
    available = [m for m in mapped if m in formulary]

    if (not disease or conf < 0.30 or not available) and symptoms.strip():
        # Keyword fallback: short real-world inputs score low on the 24-class
        # model, so fall back to transparent keyword mapping (honest tag).
        found, seen = [], set()
        for kw, meds in KEYWORD_MEDS.items():
            if kw in symptoms.lower():
                for m in meds:
                    if m in formulary and m not in seen:
                        seen.add(m)
                        found.append(m)
        if found:
            return {"suggestions": [{
                "medicine": m, "dose": FORMULARY_DOSE[m],
                "why": f"Keyword fallback (classifier {conf:.0%} — below 30% bar); in-stock",
                "in_stock": True} for m in found],
                "disease": disease, "confidence": round(conf, 3),
                "model": "rules-fallback", "abstain": False}

    if not disease or conf < 0.30 or not available:
        return {"suggestions": [], "disease": disease, "confidence": round(conf, 3),
                "model": "v0-rules", "abstain": True}

    model_tag, why_extra = "v0-rules", ""
    # Bandit reorder: only when the cluster has real feedback (n>0);
    # otherwise v0 mapping order stands (cold-start safe).
    try:
        import json as _json
        from pathlib import Path as _Path
        wp = _Path(__file__).parent / "models" / "bandit_weights.json"
        if wp.exists():
            w = _json.loads(wp.read_text())["clusters"]
            import sys as _sys
            _sys.path.insert(0, str(_Path(__file__).parent))
            from train_bandit import cluster_for
            cluster = cluster_for(symptoms, disease or "")
            info = w.get(cluster, {})
            n_total = sum(a.get("n", 0) for a in info.get("arms", {}).values())
            if n_total > 0:
                wmap = {a: info["arms"].get(a, {}).get("weight", 0) for a in available}
                available = sorted(available, key=lambda m: -wmap.get(m, 0))
                model_tag = "bandit-v1"
                why_extra = f"; learned from {n_total} past cases"
    except Exception as _e:
        print(f"Bandit reorder skipped ({_e})")

    suggestions = [{
        "medicine": m,
        "dose": FORMULARY_DOSE[m],
        "why": f"Mapped from '{disease}' ({conf:.0%} match); in-stock{why_extra}",
        "in_stock": True,
    } for m in available]
    return {"suggestions": suggestions, "disease": disease,
            "confidence": round(conf, 3), "model": model_tag, "abstain": False}
