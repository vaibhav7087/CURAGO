# Data Flow Diagram (Scenarios)

This diagram shows how data flows through the system in two distinct scenarios: **Scenario A (Normal Triage & Approval)** and **Scenario B (Escalation & Last Mile Delivery)**.

```mermaid
flowchart LR
    %% Styling
    classDef mobile fill:#dff0d8,stroke:#3c763d,stroke-width:2px;
    classDef db fill:#fcf8e3,stroke:#8a6d3b,stroke-width:2px;
    classDef core fill:#d9edf7,stroke:#31708f,stroke-width:2px;
    classDef alert fill:#f2dede,stroke:#ebccd1,stroke-width:2px;

    %% Scenario A: Triage & Approval
    subgraph "Scenario A: Triage & Approval (Digital)"
        A1(Patient Audio) -->|Dograh + Sarvam| A2(Transcribed Text)
        A2 -->|NIM LLM| A3(Extracted Medical JSON)
        A3 -->|FastAPI Webhook| A4[(Supabase TICKETS)]:::db
        A4 -->|Realtime Sync| A5[Doctor Dashboard]:::core
        A5 -->|Click 'Approve'| A6[FastAPI POST /api/approve]
        A6 -->|Twilio API| A7(Outbound SMS to Patient)
    end

    %% Scenario B: Escalation & Delivery
    subgraph "Scenario B: Escalation & Delivery (Physical)"
        B1[Doctor Dashboard]:::core -->|Click 'Send to Delivery'| B2(FastAPI POST /order)
        B2 -->|Insert| B3[(Supabase ORDERS)]:::db
        B3 -->|Fetch Pending Orders| B4[LastMileAgent Flutter App]:::mobile
        B4 -->|Agent Accepts Delivery| B5[(Update DB Status: In Transit)]
        B4 -->|Agent Delivers Meds| B6[(Update DB Status: Delivered)]
        B6 -->|Trigger Follow-up Cron| B7(FastAPI Schedule Follow-up Call):::alert
    end
```
