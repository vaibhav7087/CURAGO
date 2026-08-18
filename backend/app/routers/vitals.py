from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.database import supabase
from app.services.llm import groq_client, nim_client
import json

router = APIRouter()

class VitalsInput(BaseModel):
    temperature: Optional[str] = None
    blood_pressure: Optional[str] = None
    spo2: Optional[str] = None
    pulse: Optional[str] = None
    extra_notes: Optional[str] = None

@router.post("/{ticket_id}")
async def submit_vitals(ticket_id: str, vitals: VitalsInput):
    # 1. Fetch ticket and existing symptoms
    ticket_res = supabase.table("tickets").select("symptoms_summary, vitals_data").eq("id", ticket_id).execute()
    if not ticket_res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket = ticket_res.data[0]
    symptoms = ticket.get("symptoms_summary", "")
    existing_vitals = ticket.get("vitals_data") or {}
    
    # 2. Merge vitals
    new_vitals_dict = vitals.dict(exclude_none=True)
    merged_vitals = {**existing_vitals, **new_vitals_dict}
    
    # 3. Update DB with new vitals (so they sync to dashboard immediately)
    supabase.table("tickets").update({"vitals_data": merged_vitals}).eq("id", ticket_id).execute()
    
    # 4. LLM Interactive Diagnostic check
    if not groq_client and not nim_client:
        return {"status": "success", "vitals_saved": True, "message": "Vitals saved. AI unavailable."}
        
    prompt = f"""
    You are an expert AI doctor assisting a field trainee. 
    Patient Symptoms reported over phone: {symptoms}
    Vitals recorded physically by trainee: {json.dumps(merged_vitals)}
    
    Analyze this combined data. 
    If this is the FIRST time you are seeing this data (no 'extra_notes' provided), and you need the trainee to perform specific additional physical checks (e.g., 'Check eyes for yellowness', 'Palpate stomach'), return a JSON object with:
    {{"status": "needs_more_checks", "requested_checks": ["Check X", "Check Y"]}}
    
    CRITICAL RULE: If the trainee HAS provided 'extra_notes' in the vitals data, it means they just completed your requested checks. You MUST NOT ask for more checks. You MUST return a JSON object with:
    {{"status": "complete", "advanced_diagnosis": "Your detailed differential diagnosis based on ALL data including the extra notes..."}}
    
    Return ONLY valid JSON. No markdown formatting.
    """
    
    content = ""
    try:
        if groq_client:
            response = groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                timeout=15
            )
            content = response.choices[0].message.content
        elif nim_client:
            response = nim_client.chat.completions.create(
                model="meta/llama3-70b-instruct",
                messages=[{"role": "user", "content": prompt}],
                timeout=15
            )
            content = response.choices[0].message.content
            
    except Exception as e:
        print(f"Error with primary LLM: {e}. Falling back to NIM...")
        try:
            if nim_client:
                response = nim_client.chat.completions.create(
                    model="meta/llama3-70b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    timeout=15
                )
                content = response.choices[0].message.content
            else:
                return {"status": "error", "vitals_saved": True, "message": "Failed to generate AI analysis."}
        except Exception as fallback_e:
            print(f"Error in fallback NIM: {fallback_e}")
            return {"status": "error", "vitals_saved": True, "message": "Failed to generate AI analysis."}

    if not content:
        return {"status": "error", "vitals_saved": True, "message": "No response from AI."}

    try:
        cleaned_content = content.replace('```json', '').replace('```', '').strip()
        result = json.loads(cleaned_content)
        
        # If complete, update the ticket with advanced diagnosis and escalate to doctor
        if result.get("status") == "complete":
            adv_diag = result.get("advanced_diagnosis")
            supabase.table("tickets").update({
                "extracted_symptoms": {"advanced_diagnosis": adv_diag},
                "status": "doctor_review"
            }).eq("id", ticket_id).execute()
            
        return result
        
    except Exception as e:
        print(f"Error parsing vitals AI analysis: {e}")
        return {"status": "error", "vitals_saved": True, "message": "Failed to parse AI analysis."}
