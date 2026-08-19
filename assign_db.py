
import sys, os
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
from app.core.database import supabase

# Get the latest approved ticket
res = supabase.table('tickets').select('*').order('created_at', desc=True).limit(1).execute()
if res.data:
    t_id = res.data[0]['id']
    # Update to needs_vitals and assign trainee
    supabase.table('tickets').update({
        'status': 'needs_vitals', 
        'assigned_trainee_id': '11111111-1111-1111-1111-111111111111'
    }).eq('id', t_id).execute()
    print('Successfully assigned trainee to ticket:', t_id)

