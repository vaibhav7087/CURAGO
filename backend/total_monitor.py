import time
import sys
import os
import re
from datetime import datetime
from app.core.database import supabase

def tail_file(filename):
    """Generator to continuously yield new lines from a file."""
    try:
        # Seek to the end of the file
        with open(filename, 'r', encoding='utf-16', errors='ignore') as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                yield line
    except FileNotFoundError:
        # If utf-16 fails or file missing, fallback to utf-8
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                yield line

def get_latest_ticket():
    try:
        res = supabase.table("tickets").select("*, patients(*)").order("created_at", desc=True).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return None

def main():
    print("\n" + "="*80)
    print(" 🚀 [CURAGO TOTAL MONITORING SYSTEM ACTIVE] 🚀")
    print(" Watching: Webhooks, Transcripts, LLM Intelligence, and Database Updates")
    print("="*80 + "\n")
    
    server_log_path = "server.log"
    if not os.path.exists(server_log_path):
        print(f"Waiting for {server_log_path} to be created...")
        while not os.path.exists(server_log_path):
            time.sleep(1)
            
    print(f"Tailing {server_log_path}...")
    
    latest_ticket = get_latest_ticket()
    last_ticket_id = latest_ticket['id'] if latest_ticket else None
    
    log_generator = tail_file(server_log_path)
    
    # State tracking
    current_call = {
        "webhook_hit": False,
        "transcript_len": 0,
        "llm_started": False,
        "llm_result": None,
        "errors": []
    }
    
    print("\n⏳ Waiting for next phone call to finish...\n")
    
    while True:
        # 1. Read one new line from log
        try:
            line = next(log_generator)
            line = line.strip()
            
            if "DEBUG: Webhook received payload keys" in line:
                current_call["webhook_hit"] = True
                print(f"\n[WEBHOOK] 🌐 Incoming request from Vapi at {datetime.now().strftime('%H:%M:%S')}")
                
            if "DEBUG: message type:" in line:
                msg_type = line.split("type: ")[-1]
                print(f"[WEBHOOK] 📨 Event type: {msg_type}")
                
            if "DEBUG: Ignoring intermediate Vapi event" in line:
                print(f"[WEBHOOK] ⏭️ Skipped intermediate event to avoid blank tickets.")
                
            if "Call" in line and "ended. Processing patient" in line:
                print(f"\n[PIPELINE] ⚙️ Processing final end-of-call report...")
                
            if "transcript preview:" in line:
                preview = line.split("preview: ")[-1]
                print(f"[TRANSCRIPT] 📝 Raw Transcript Preview: {preview}")
                
            if "Attempting extraction with NVIDIA NIM" in line:
                current_call["llm_started"] = True
                print(f"[LLM] 🧠 Sending transcript to NVIDIA NIM for intelligence extraction...")
                
            if "Webhook Error" in line or "Exception" in line or "Error" in line:
                # Basic error filter
                if "DEBUG" not in line and "INFO" not in line:
                    current_call["errors"].append(line)
                    print(f"[ERROR] 🚨 {line}")
                    
        except Exception as e:
            pass
            
        # 2. Check Database for new ticket
        curr_ticket = get_latest_ticket()
        if curr_ticket and curr_ticket['id'] != last_ticket_id:
            print("\n[DATABASE] 💾 New ticket successfully saved to Supabase!")
            
            t = curr_ticket
            p = t.get("patients") or {}
            
            print("\n" + "="*80)
            print(" 🏥 FINAL DASHBOARD DATA ANALYSIS")
            print("="*80)
            
            # Diagnostic logic
            name_issue = ""
            if p.get('name') == 'Unknown Patient' or not p.get('name'):
                name_issue = "⚠️ WARNING: Username was NOT set! The LLM failed to extract the name from the transcript, or the transcript was empty."
                
            print(f"Ticket ID      : {t.get('id')}")
            print(f"Patient Name   : {p.get('name')} {name_issue}")
            print(f"Phone Number   : {p.get('phone_number')}")
            print(f"Age / Gender   : {p.get('age')} / {p.get('gender')}")
            print(f"Village        : {p.get('village')}")
            print(f"Symptoms       : {t.get('symptoms_summary')}")
            print(f"Triage Severity: {t.get('severity')}")
            print(f"Status         : {t.get('status')}")
            print("="*80 + "\n")
            
            # Reset state for next call
            last_ticket_id = curr_ticket['id']
            current_call = {
                "webhook_hit": False,
                "transcript_len": 0,
                "llm_started": False,
                "llm_result": None,
                "errors": []
            }
            print("⏳ Waiting for next phone call to finish...\n")
            
if __name__ == "__main__":
    main()
