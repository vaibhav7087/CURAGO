import os
import sys
import time
import random
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv(".env")

from app.core.database import supabase

# A list of valid trainee UUIDs (in a real app, this would be fetched from a 'trainees' table)
TRAINEE_IDS = [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222"
]

def run_scheduler():
    print("Starting Follow-Up Scheduler...")
    
    while True:
        print("Checking for patients needing follow-up vitals...")
        
        # 1. Fetch open tickets that are NOT yet assigned
        res = supabase.table("tickets").select("*").eq("status", "open").is_("assigned_trainee_id", "null").execute()
        unassigned_tickets = res.data
        
        assigned_count = 0
        for ticket in unassigned_tickets:
            summary = str(ticket.get("symptoms_summary", "")).lower()
            
            # 2. Check if the summary indicates the patient is not fully recovered
            needs_follow_up = False
            keywords = ["not recovered", "not fully recovered", "follow up", "follow-up", "still sick", "worse", "no improvement"]
            
            if any(k in summary for k in keywords):
                needs_follow_up = True
                
            if needs_follow_up:
                # 3. Assign a random trainee
                random_trainee = random.choice(TRAINEE_IDS)
                ticket_id = ticket["id"]
                
                print(f"Patient needs follow-up (Ticket {ticket_id}). Assigning to trainee {random_trainee}...")
                
                supabase.table("tickets").update({
                    "assigned_trainee_id": random_trainee,
                    "status": "needs_vitals"
                }).eq("id", ticket_id).execute()
                
                assigned_count += 1
                
        print(f"Finished cycle. Assigned {assigned_count} follow-ups. Sleeping for 30s...")
        time.sleep(30)

if __name__ == "__main__":
    run_scheduler()
