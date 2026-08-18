from fastapi import APIRouter, Request, HTTPException
import traceback
from app.core.database import supabase
from app.services.llm import search_medical_knowledge, extract_patient_data

router = APIRouter()

@router.post("/rag/search")
async def rag_search(request: Request):
    """Called mid-call by Dograh as a tool to fetch guidelines."""
    try:
        body = await request.json()
        
        # Parse Vapi tool-call payload
        if "message" in body and body["message"].get("type") == "tool-calls":
            tool_calls = body["message"].get("toolWithToolCallList", [])
            if tool_calls and "toolCall" in tool_calls[0]:
                args = tool_calls[0]["toolCall"].get("function", {}).get("arguments", {})
                query = args.get("query", "")
            else:
                query = ""
        # Fallback to Dograh payload
        else:
            query = body.get("query", "")

        if not query:
            return {"results": [{"content": "No query provided.", "similarity": 0}]}
        
        print(f"AI is searching database for: {query}")
        results = await search_medical_knowledge(query)
        
        # Vapi expects result to be returned in a specific tool-call response format,
        # but returning a standard JSON object is also generally parsed correctly by the LLM.
        return {"results": results}
    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"RAG Search Endpoint Error: {e}\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vapi-tool")
async def vapi_tool_handler(request: Request):
    """General endpoint for Vapi tool calls."""
    try:
        body = await request.json()
        
        if "message" in body and body["message"].get("type") == "tool-calls":
            tool_calls = body["message"].get("toolWithToolCallList", [])
            responses = []
            
            for tool_call_wrapper in tool_calls:
                tool_call = tool_call_wrapper.get("toolCall", {})
                function_name = tool_call.get("function", {}).get("name")
                arguments = tool_call.get("function", {}).get("arguments", {})
                call_id = tool_call.get("id")
                
                if function_name == "get_patient_history":
                    # Get caller's phone number from the top level call object if not explicitly passed
                    phone_number = body["message"].get("call", {}).get("customer", {}).get("number")
                    if not phone_number:
                        phone_number = arguments.get("phone_number")
                        
                    print(f"Fetching history for phone number: {phone_number}")
                    
                    if not phone_number:
                        responses.append({"toolCallId": call_id, "result": "No phone number provided."})
                        continue
                        
                    # 1. Fetch patient
                    patient_res = supabase.table("patients").select("id, name").eq("phone_number", phone_number).execute()
                    if not patient_res.data:
                        responses.append({"toolCallId": call_id, "result": "No patient history found for this phone number."})
                        continue
                        
                    patient_id = patient_res.data[0]["id"]
                    patient_name = patient_res.data[0].get("name", "Unknown")
                    
                    # 2. Fetch latest ticket
                    ticket_res = supabase.table("tickets").select("symptoms_summary, status").eq("patient_id", patient_id).order("created_at", desc=True).limit(1).execute()
                    
                    if not ticket_res.data:
                        responses.append({"toolCallId": call_id, "result": f"Patient {patient_name} found, but no past medical tickets exist."})
                        continue
                        
                    latest_ticket = ticket_res.data[0]
                    summary = latest_ticket.get("symptoms_summary", "No symptoms recorded")
                    
                    result_text = f"Patient Name: {patient_name}. Previous Symptoms: {summary}."
                    responses.append({
                        "toolCallId": call_id,
                        "result": result_text
                    })
            
            return {"results": responses}
            
        return {"status": "ignored"}
    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"Vapi Tool Error: {e}\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/end-call")
async def end_call_webhook(request: Request):
    """Called at the end of the call to create a ticket (Supports Dograh and Vapi)."""
    try:
        payload = await request.json()
        
        # 0. Fast-fail for Vapi intermediate events
        if "message" in payload:
            msg_type = payload["message"].get("type")
            if msg_type != "end-of-call-report":
                print(f"DEBUG: Ignoring intermediate Vapi event: {msg_type}")
                return {"status": "ignored", "reason": f"intermediate event {msg_type}"}

        print(f"DEBUG: Webhook received payload keys: {list(payload.keys())}")
        if "message" in payload:
            print(f"DEBUG: message keys: {list(payload['message'].keys())}")
            print(f"DEBUG: message type: {payload['message'].get('type')}")
            # The transcript in end-of-call-report is typically inside the artifact or at the top level
            artifact = payload["message"].get("artifact", {})
            print(f"DEBUG: transcript preview: {artifact.get('transcript', '')[:100]}")

        # Vapi Payload Parsing
        if "message" in payload and payload["message"].get("type") == "end-of-call-report":
            msg = payload["message"]
            call_id = msg.get("call", {}).get("id", "Unknown")
            caller_number = msg.get("call", {}).get("customer", {}).get("number", "Unknown")
            # Transcript can be in msg.artifact.messagesOpenAIFormatted or msg.artifact.transcript
            artifact = msg.get("artifact", {})
            
            # Extract transcript from OpenAI formatted messages if available
            messages = artifact.get("messagesOpenAIFormatted", [])
            if messages:
                transcript_parts = []
                for m in messages:
                    role = m.get("role", "unknown")
                    content = m.get("content", "")
                    transcript_parts.append(f"{role.capitalize()}: {content}")
                transcript = "\n".join(transcript_parts)
            else:
                transcript = artifact.get("transcript", "")
            
            gathered_data = msg.get("analysis", {}).get("structuredData", {}) or {}
            
        # Also check top-level Vapi payload if not nested under message
        elif payload.get("type") == "end-of-call-report":
            call_id = payload.get("call", {}).get("id", "Unknown")
            caller_number = payload.get("call", {}).get("customer", {}).get("number", "Unknown")
            transcript = payload.get("transcript", "")
            gathered_data = payload.get("analysis", {}).get("structuredData", {}) or {}
            
        # Dograh Payload Parsing
        else:
            call_id = payload.get("call_id", "Unknown")
            caller_number = payload.get("caller_number", "Unknown")
            transcript = payload.get("transcript", "")
            gathered_data = payload.get("gathered_data", {}) or {}

        print(f"Call {call_id} ended. Processing patient {caller_number}. Transcript length: {len(transcript)} chars.")

        # 1. Extract data
        patient_name = gathered_data.get("patient_name")
        severity = gathered_data.get("severity")
        symptoms = gathered_data.get("symptoms")
        age = gathered_data.get("age")
        gender = gathered_data.get("gender")
        village = gathered_data.get("village")

        # We ALWAYS run our backend LLM extraction now because:
        # 1. It translates regional languages to English.
        # 2. It suggests medicines based on our custom inventory.
        # 3. It extracts missing fields like 'village' that Vapi might miss.
        print("Running backend LLM extraction for translation, location, and medicine suggestions...")
        extracted = extract_patient_data(transcript)
        
        # Merge Vapi's data with our LLM's data (LLM takes precedence if Vapi missed it)
        patient_name = extracted.get("patient_name") or patient_name or "Unknown Patient"
        severity = extracted.get("severity") or severity or "Medium"
        symptoms = extracted.get("symptoms") or symptoms or "Unspecified symptoms"
        if isinstance(symptoms, list):
            symptoms = ", ".join(symptoms)
            
        age = extracted.get("age") or age
        gender = extracted.get("gender") or gender
        village = extracted.get("village") or village
        
        suggested_meds = extracted.get("suggested_medicines")
        if suggested_meds and isinstance(suggested_meds, list):
                meds_str = ", ".join(suggested_meds)
                symptoms = f"{symptoms}\n\nAI Recommended Medicines: {meds_str}"

        # 2. Upsert Patient
        existing = supabase.table("patients").select("id").eq("phone_number", caller_number).execute()
        
        if existing.data:
            p_id = existing.data[0]['id']
            # Update patient info (coalescing to avoid overriding good data with nulls)
            update_data = {}
            if patient_name and patient_name != "Unknown Patient": update_data["name"] = patient_name
            if age: update_data["age"] = age
            if gender: update_data["gender"] = gender
            if village: update_data["village"] = village
            
            if update_data:
                supabase.table("patients").update(update_data).eq("id", p_id).execute()
                print(f"Updated existing patient: {patient_name}")
        else:
            patient_data = {
                "name": patient_name or "Unknown Patient",
                "phone_number": caller_number,
                "age": age,
                "gender": gender,
                "village": village
            }
            new_p = supabase.table("patients").insert(patient_data).execute()
            p_id = new_p.data[0]['id']
            print(f"Registered new patient: {patient_name}")

        # 3. Deduplicate and Create Ticket
        # Vapi might retry the webhook if it times out, causing duplicates.
        # We check if there's an open ticket created in the last 2 minutes for this patient.
        recent_tickets = supabase.table("tickets").select("id").eq("patient_id", p_id).order("created_at", desc=True).limit(1).execute()
        
        if recent_tickets.data:
            # Check if we should skip creating a duplicate
            ticket_id = recent_tickets.data[0]['id']
            print(f"Skipping duplicate ticket creation, returning existing ticket: {ticket_id}")
            return {"status": "ok", "ticket_id": ticket_id, "note": "deduplicated"}
            
        ticket_res = supabase.table("tickets").insert({
            "patient_id": p_id, 
            "symptoms_summary": symptoms,
            "severity": severity,
            "status": "open"
        }).execute()
        
        ticket_id = ticket_res.data[0]['id']
        print(f"Ticket created for {patient_name} with {severity} severity.")
        
        return {"status": "ok", "ticket_id": ticket_id}

    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"Webhook Error: {e}\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=str(e))
