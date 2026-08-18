-- curago/setup_supabase.sql
-- V2 Schema — Single Supabase instance for App Data + RAG

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    phone_number TEXT,
    age INTEGER,
    gender TEXT,
    village TEXT,
    address_lat FLOAT,
    address_lng FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    status TEXT DEFAULT 'open',              -- open, assigned, resolved, escalated
    severity TEXT,                            -- high, medium, low
    symptoms_summary TEXT,
    extracted_symptoms JSONB,
    vitals_data JSONB,
    assigned_trainee_id UUID,
    camp_id UUID,                            -- FK added below after camps table exists
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Orders / Delivery Table
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES tickets(id),
    patient_phone TEXT,                      -- Denormalized for quick Twilio SMS dispatch
    patient_name TEXT,                       -- Denormalized for Flutter app display
    status TEXT DEFAULT 'Pending',           -- Pending, In Transit, Delivered
    shift TEXT,                              -- Morning, Evening
    total_amount TEXT,
    cod_amount TEXT,
    package_items JSONB,                     -- [{name, quantity}]
    delivery_address TEXT,
    delivery_agent_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    center_id TEXT,                          -- L1_Village, L2_Cluster, L3_District
    medicine_name TEXT NOT NULL,
    stock INTEGER DEFAULT 0,
    unit TEXT,
    description TEXT,
    type TEXT,                               -- high, low, normal (stock level)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Camps Table (Specialist Escalation)
CREATE TABLE IF NOT EXISTS camps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    specialty TEXT,                           -- eye, diabetes, cardio
    date TEXT,
    max_capacity INTEGER DEFAULT 50,
    booked_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add FK from tickets to camps (now that camps table exists)
ALTER TABLE tickets ADD CONSTRAINT fk_tickets_camp
    FOREIGN KEY (camp_id) REFERENCES camps(id);

-- 6. RAG Knowledge Base Table
-- Uses Gemini text-embedding-004 (768 dims)
-- This is independent of the NIM/Groq chat LLM fallback
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(768)
);

-- 7. Match Documents Function (for RAG vector search)
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    knowledge_base.id,
    knowledge_base.content,
    knowledge_base.metadata,
    1 - (knowledge_base.embedding <=> query_embedding) AS similarity
  FROM knowledge_base
  WHERE 1 - (knowledge_base.embedding <=> query_embedding) > match_threshold
  ORDER BY knowledge_base.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Disable RLS for hackathon (no auth complications)
ALTER TABLE patients DISABLE ROW LEVEL SECURITY;
ALTER TABLE tickets DISABLE ROW LEVEL SECURITY;
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
ALTER TABLE inventory DISABLE ROW LEVEL SECURITY;
ALTER TABLE camps DISABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base DISABLE ROW LEVEL SECURITY;
