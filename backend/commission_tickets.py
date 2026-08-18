import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv(".env")

from app.core.database import supabase

def commission_some_tickets():
    print("Fetching tickets...")
    res = supabase.table("tickets").select("id").execute()
    tickets = res.data
    
    if len(tickets) >= 4:
        # 1. Doctor assigned trainee to these two
        print("Assigning trainee to 2 tickets...")
        dummy_uuid = "11111111-1111-1111-1111-111111111111"
        supabase.table("tickets").update({"assigned_trainee_id": dummy_uuid}).eq("id", tickets[0]["id"]).execute()
        supabase.table("tickets").update({"assigned_trainee_id": dummy_uuid}).eq("id", tickets[1]["id"]).execute()
        
        # 2. Follow-up summary states patient not fully recovered (status = needs_vitals)
        print("Flagging 2 tickets as needs_vitals...")
        supabase.table("tickets").update({"status": "needs_vitals"}).eq("id", tickets[2]["id"]).execute()
        supabase.table("tickets").update({"status": "needs_vitals"}).eq("id", tickets[3]["id"]).execute()
        
        print("Successfully commissioned 4 tickets for vitals collection.")
    else:
        print("Not enough tickets found. Did you run the seed script?")

if __name__ == "__main__":
    commission_some_tickets()
