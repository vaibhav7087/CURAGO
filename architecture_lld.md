# Low-Level Design (LLD)

This document contains two detailed sequence diagrams covering the two core real-time flows in the system.

## Diagram 1: The AI Call Flow (Inbound → Triage → Ticket)

```mermaid
sequenceDiagram
    actor Patient
    participant Twilio
    participant Dograh
    participant Sarvam STT
    participant NIM LLM
    participant FastAPI
    participant Supabase DB
    participant Sarvam TTS

    Patient->>Twilio: Dials Helpline
    Twilio->>Dograh: Webhook (Incoming Call)
    Dograh->>Twilio: Accept & Open WebSocket
    
    loop Conversation Loop
        Patient->>Twilio: Speaks (Audio)
        Twilio->>Dograh: Streams Audio
        Dograh->>Sarvam STT: Raw Audio bytes
        Sarvam STT-->>Dograh: Transcribed Text (Hindi/English)
        
        Dograh->>NIM LLM: Prompt + Transcribed Text
        
        alt RAG Tool Call Triggered
            NIM LLM-->>Dograh: Tool Call (search_medical_knowledge)
            Dograh->>FastAPI: POST /api/rag/search {query}
            FastAPI->>Supabase DB: Gemini Embedding → RPC match_documents
            Supabase DB-->>FastAPI: Top 5 medical results
            FastAPI-->>Dograh: JSON Results
            Dograh->>NIM LLM: Tool Response (Remedies)
        end
        
        NIM LLM-->>Dograh: Final Text Response
        Dograh->>Sarvam TTS: Text Response
        Sarvam TTS-->>Dograh: Audio Bytes
        Dograh->>Twilio: Stream Audio Bytes
        Twilio->>Patient: Hears Voice
    end

    Patient->>Twilio: Hangs up
    Twilio->>Dograh: Call Ended
    Dograh->>FastAPI: POST /api/webhook/end-call (Transcript + Gathered Data)
    FastAPI->>NIM LLM: Extract patient data (if gathered_data is empty)
    FastAPI->>Supabase DB: UPSERT patients, INSERT tickets
    FastAPI-->>Dograh: {status: ok, ticket_id}
```

## Diagram 2: Doctor Approval → SMS → Delivery → Follow-up

```mermaid
sequenceDiagram
    actor Doctor
    participant Dashboard as React Dashboard
    participant FastAPI
    participant Supabase
    participant Twilio
    actor Patient
    participant FlutterApp as LastMileAgent App
    actor DeliveryAgent

    Note over Dashboard,Supabase: Supabase Realtime pushes new ticket to Dashboard

    Doctor->>Dashboard: Reviews AI summary, selects medicines
    Doctor->>Dashboard: Clicks "Approve & Dispatch"
    Dashboard->>FastAPI: POST /api/approve {ticket_id, medicines, patient_phone, shift}
    FastAPI->>Supabase: UPDATE tickets SET status='resolved'
    FastAPI->>Supabase: INSERT INTO orders (patient_phone, package_items, shift)
    FastAPI->>Twilio: Send SMS "Your prescription is approved..."
    Twilio->>Patient: SMS delivered
    FastAPI-->>Dashboard: {order_id, sms_sent: true}
    Dashboard->>Doctor: Toast: "Approved & SMS Sent!"

    DeliveryAgent->>FlutterApp: Opens app
    FlutterApp->>Supabase: SELECT * FROM orders WHERE status='Pending'
    Supabase-->>FlutterApp: Pending orders list
    DeliveryAgent->>FlutterApp: Taps "Accept"
    FlutterApp->>Supabase: UPDATE orders SET status='In Transit'
    DeliveryAgent->>FlutterApp: Delivers meds, taps "Delivered"
    FlutterApp->>Supabase: UPDATE orders SET status='Delivered'
    
    Note over FastAPI,Twilio: Follow-up triggered on delivery
    FastAPI->>Twilio: Send follow-up SMS "Medicines delivered. Contact us if symptoms persist."
    Twilio->>Patient: Follow-up SMS
```
