import sys, os
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
from app.core.database import supabase

res = supabase.table('tickets').select('*').order('created_at', desc=True).limit(5).execute()
for t in res.data:
    print("ID:", t['id'], "Status:", t['status'], "Trainee:", t['assigned_trainee_id'])
