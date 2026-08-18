# Entity Relationship (ER) Diagram

This represents the complete database schema for V2, supporting the React Dashboard, the Flutter LastMileAgent app, the RAG knowledge base, and the specialist camp escalation flow.

```mermaid
erDiagram
    PATIENTS {
        uuid id PK
        text name
        text phone_number
        int age
        text gender
        text village
        float address_lat
        float address_lng
        timestamptz created_at
    }

    TICKETS {
        uuid id PK
        uuid patient_id FK
        text status "open | assigned | resolved | escalated"
        text severity "high | medium | low"
        text symptoms_summary
        jsonb extracted_symptoms
        jsonb vitals_data
        uuid assigned_trainee_id
        timestamptz created_at
        timestamptz updated_at
    }

    ORDERS {
        uuid id PK
        uuid ticket_id FK
        text patient_phone "denormalized for quick SMS"
        text patient_name "denormalized for Flutter display"
        text status "Pending | In Transit | Delivered"
        text shift "Morning | Evening"
        text total_amount
        text cod_amount
        jsonb package_items "Array of medicines"
        text delivery_address
        uuid delivery_agent_id
        timestamptz created_at
    }

    INVENTORY {
        uuid id PK
        text center_id "L1_Village | L2_Cluster | L3_District"
        text medicine_name
        int stock
        text unit
        text description
        text type "high | low | normal"
        timestamptz created_at
    }

    CAMPS {
        uuid id PK
        text name
        text specialty "eye | diabetes | cardio"
        text date
        int max_capacity
        int booked_count
        timestamptz created_at
    }

    KNOWLEDGE_BASE {
        uuid id PK
        text content
        jsonb metadata "type: symptom or remedy"
        vector embedding "768 dims (Gemini text-embedding-004)"
    }

    PATIENTS ||--o{ TICKETS : "has"
    TICKETS ||--o| ORDERS : "generates"
    TICKETS }o--o| CAMPS : "escalated to"
    INVENTORY }o--|| ORDERS : "sourced for (via package_items)"
```
