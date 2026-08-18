import time
import sys
import os
from app.core.database import supabase

print("=== [LIVE CALL MONITOR & DEBUGGER ACTIVE] ===", flush=True)
print("Listening for incoming call completion, transcript, and ticket details...", flush=True)

try:
    initial = supabase.table("tickets").select("id").order("created_at", desc=True).limit(1).execute()
    last_id = initial.data[0]["id"] if initial.data else None
except Exception:
    last_id = None

print("Ready. Waiting for your live call to conclude...\n", flush=True)

for i in range(180):  # Monitor for 6 minutes
    time.sleep(2)
    try:
        res = supabase.table("tickets").select("*, patients(*)").order("created_at", desc=True).limit(1).execute()
        if res.data and res.data[0]["id"] != last_id:
            t = res.data[0]
            p = t.get("patients") or {}
            print("\n" + "="*60, flush=True)
            print(">>> LIVE CALL FINISHED & PROCESSED BY BACKEND! <<<", flush=True)
            print(f"Ticket ID      : {t.get('id')}", flush=True)
            print(f"Patient Name   : {p.get('name')}", flush=True)
            print(f"Phone Number   : {p.get('phone_number')}", flush=True)
            print(f"Age / Gender   : {p.get('age')} / {p.get('gender')}", flush=True)
            print(f"Village        : {p.get('village')}", flush=True)
            print(f"Symptoms Summary: {t.get('symptoms_summary')}", flush=True)
            print(f"Triage Severity: {t.get('severity')}", flush=True)
            print(f"Status         : {t.get('status')}", flush=True)
            print("="*60 + "\n", flush=True)
            last_id = t.get('id')
            break
    except Exception:
        pass
