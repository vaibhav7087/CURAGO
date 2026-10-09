
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv('.env')

from app.core.database import supabase

TRAINEE_ID = '11111111-1111-1111-1111-111111111111'
TARGET_TASKS = 4


def seed():
    print('Seeding trainee home-visit tasks...')

    res = supabase.table('tickets').select(
        'id, status, assigned_trainee_id, vitals_data, patients(name)'
    ).execute()
    tickets = res.data

    def patient_name(t):
        return (t.get('patients') or {}).get('name')

    mine = [t for t in tickets
            if t['status'] == 'open' and t.get('assigned_trainee_id') == TRAINEE_ID]
    pool = [t for t in tickets
            if t['status'] == 'open'
            and not t.get('assigned_trainee_id')
            and patient_name(t) not in (None, '', 'Unknown Patient')]

    # Release unidentified-patient tasks so every visit shows a real name
    for t in mine:
        if patient_name(t) in (None, '', 'Unknown Patient'):
            supabase.table('tickets').update(
                {'assigned_trainee_id': None}).eq('id', t['id']).execute()
            print(f'  released unidentified task {t["id"]}')
            mine.remove(t)

    print(f'Already assigned to trainee: {len(mine)} | usable pool: {len(pool)}')

    need = TARGET_TASKS - len(mine)
    for t in pool[:max(0, need)]:
        supabase.table('tickets').update({
            'assigned_trainee_id': TRAINEE_ID,
            'vitals_data': t.get('vitals_data') or {}
        }).eq('id', t['id']).execute()
        print(f'  assigned open ticket {t["id"]} ({patient_name(t)})')

    final = supabase.table('tickets') \
        .select('id, status, assigned_trainee_id, vitals_data') \
        .eq('assigned_trainee_id', TRAINEE_ID) \
        .eq('status', 'open').execute().data
    print(f'Trainee tasks now: {len(final)}')
    for t in final:
        recorded = bool(t.get('vitals_data'))
        print(f'  - {t["id"][:8]} vitals={"Done" if recorded else "Pending"}')


if __name__ == '__main__':
    seed()
