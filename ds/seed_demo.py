"""
ds/seed_demo.py — Seed demo data (inventory, camps, knowledge_base).
Idempotent: inserts only when tables are empty. Writes to LIVE Supabase.
Run: py -3.11 ds/seed_demo.py  (from repo root)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from dotenv import load_dotenv

load_dotenv("backend/.env")
from supabase import create_client
import pandas as pd

sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

INVENTORY = [
    {"medicine_name": "Paracetamol 500mg", "stock": 240, "unit": "tablets", "type": "normal", "center_id": "L1_Village", "description": "Fever and pain relief"},
    {"medicine_name": "Amoxicillin 250mg", "stock": 45, "unit": "capsules", "type": "normal", "center_id": "L1_Village", "description": "Antibiotic for infections"},
    {"medicine_name": "Ibuprofen 400mg", "stock": 5, "unit": "tablets", "type": "low", "center_id": "L1_Village", "description": "NSAID for swelling"},
    {"medicine_name": "Ceftriaxone Inj 1g", "stock": 12, "unit": "vials", "type": "normal", "center_id": "L2_Cluster", "description": "IV antibiotic"},
    {"medicine_name": "ORS Packets", "stock": 50, "unit": "packets", "type": "normal", "center_id": "L1_Village", "description": "Rehydration salts"},
]

CAMPS = [
    {"name": "Eye Care Camp", "specialty": "eye", "date": "2026-10-12", "max_capacity": 50, "booked_count": 0},
    {"name": "Diabetes Screening Camp", "specialty": "diabetes", "date": "2026-10-19", "max_capacity": 50, "booked_count": 0},
    {"name": "Cardio Checkup Camp", "specialty": "cardio", "date": "2026-10-26", "max_capacity": 40, "booked_count": 0},
]


def seed_simple(table, rows, label):
    n = sb.table(table).select("id", count="exact").limit(1).execute().count or 0
    if n > 0:
        print(f"{table}: already has {n} rows, skipping")
        return
    sb.table(table).insert(rows).execute()
    print(f"{table}: inserted {len(rows)} rows")


def seed_knowledge(n_rows=15):
    n = sb.table("knowledge_base").select("id", count="exact").limit(1).execute().count or 0
    if n > 0:
        print(f"knowledge_base: already has {n} rows, skipping")
        return
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    emb_cfg = types.EmbedContentConfig(output_dimensionality=768)
    df = pd.read_csv("knowledge_base/Home Remedies.csv").head(n_rows)
    rows = []
    for _, r in df.iterrows():
        content = f"To treat {r['Health Issue']}: {r['Home Remedy']}"
        emb = client.models.embed_content(model="gemini-embedding-001", contents=content, config=emb_cfg)
        vec = list(emb.embeddings[0].values)
        rows.append({"content": content,
                     "metadata": {"type": "remedy", "issue": str(r["Health Issue"])},
                     "embedding": vec})
    sb.table("knowledge_base").insert(rows).execute()
    print(f"knowledge_base: inserted {len(rows)} rows")


if __name__ == "__main__":
    seed_simple("inventory", INVENTORY, "inventory")
    seed_simple("camps", CAMPS, "camps")
    seed_knowledge()
    print("seed-demo-done")
