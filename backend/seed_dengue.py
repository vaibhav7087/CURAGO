
import os
import sys
import uuid
import random
import time
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv('.env')

from app.core.database import supabase

def seed():
    print('Seeding Dengue pandemic dummy data with orders...')
    
    patients = [
        {'name': 'Aarav Patel', 'phone_number': '919876543210', 'village': 'Palampur', 'age': 28, 'gender': 'Male'},
        {'name': 'Diya Sharma', 'phone_number': '919876543211', 'village': 'Palampur', 'age': 34, 'gender': 'Female'},
        {'name': 'Vihaan Singh', 'phone_number': '919876543212', 'village': 'Kothrud', 'age': 45, 'gender': 'Male'},
        {'name': 'Aditi Verma', 'phone_number': '919876543213', 'village': 'Kothrud', 'age': 22, 'gender': 'Female'},
        {'name': 'Arjun Reddy', 'phone_number': '919876543214', 'village': 'Malviya Nagar', 'age': 55, 'gender': 'Male'},
        {'name': 'Neha Gupta', 'phone_number': '919876543215', 'village': 'Malviya Nagar', 'age': 31, 'gender': 'Female'},
        {'name': 'Sai Krishna', 'phone_number': '919876543216', 'village': 'Banjara Hills', 'age': 40, 'gender': 'Male'},
        {'name': 'Ananya Desai', 'phone_number': '919876543217', 'village': 'Andheri', 'age': 29, 'gender': 'Female'},
        {'name': 'Rohan Iyer', 'phone_number': '919876543218', 'village': 'Andheri', 'age': 50, 'gender': 'Male'},
        {'name': 'Kavya Pillai', 'phone_number': '919876543219', 'village': 'Koramangala', 'age': 26, 'gender': 'Female'},
        {'name': 'Kabir Das', 'phone_number': '919876543220', 'village': 'Salt Lake', 'age': 38, 'gender': 'Male'},
        {'name': 'Meera Joshi', 'phone_number': '919876543221', 'village': 'Salt Lake', 'age': 47, 'gender': 'Female'},
        {'name': 'Ishaan Kumar', 'phone_number': '919876543222', 'village': 'Vasant Kunj', 'age': 33, 'gender': 'Male'},
        {'name': 'Sanya Malhotra', 'phone_number': '919876543223', 'village': 'Vasant Kunj', 'age': 25, 'gender': 'Female'},
        {'name': 'Vivaan Kapoor', 'phone_number': '919876543224', 'village': 'Saket', 'age': 62, 'gender': 'Male'},
        {'name': 'Tara Nair', 'phone_number': '919876543225', 'village': 'Saket', 'age': 19, 'gender': 'Female'},
        {'name': 'Ayaan Khan', 'phone_number': '919876543226', 'village': 'Gomti Nagar', 'age': 27, 'gender': 'Male'},
        {'name': 'Riya Mukherjee', 'phone_number': '919876543227', 'village': 'Gomti Nagar', 'age': 41, 'gender': 'Female'},
    ]
    
    dengue_symptoms = [
        'High fever, severe joint pain, skin rash',
        'High fever, pain behind the eyes, severe headache',
        'Sudden high fever, nausea, vomiting, muscle ache',
        'High fever, extreme fatigue, bleeding gums',
        'Fever, severe abdominal pain, rapid breathing',
        'Fever, persistent vomiting, blood in vomit',
        'High fever, severe muscle and joint pain (breakbone fever)',
        'Fever, fatigue, mild rash on arms and legs'
    ]
    
    statuses = (
        ['open'] * 4 +
        ['needs_vitals'] * 3 +
        ['doctor_review'] * 4 +
        ['approved'] * 3 +
        ['closed'] * 2 +
        ['follow_up'] * 2
    )
    random.shuffle(statuses)
    
    trainee_id = '11111111-1111-1111-1111-111111111111'
    
    print('Clearing old records for a clean demo...')
    supabase.table('orders').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    supabase.table('tickets').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    supabase.table('patients').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    
    for i, p in enumerate(patients):
        res = supabase.table('patients').insert(p).execute()
        patient_id = res.data[0]['id']
        
        status = statuses[i]
        symptoms = random.choice(dengue_symptoms)
        
        ticket = {
            'patient_id': patient_id,
            'symptoms_summary': symptoms,
            'severity': random.choice(['Medium', 'High', 'High']),
            'status': status,
            'vitals_data': {}
        }
        
        if status in ['needs_vitals', 'doctor_review', 'approved', 'closed', 'follow_up']:
            ticket['assigned_trainee_id'] = trainee_id
        
        if status in ['doctor_review', 'approved', 'closed', 'follow_up']:
            ticket['vitals_data'] = {
                'temperature': str(random.randint(101, 104)) + '.0',
                'blood_pressure': '110/70',
                'spo2': str(random.randint(94, 98)),
                'extra_notes': 'Patient looks very weak, possible dehydration.'
            }
            
            ticket['extracted_symptoms'] = {
                'advanced_diagnosis': '**Likely Diagnosis**\n- Clinical presentation is highly suspicious for Dengue Fever.\n\n**Key Findings**\n- High fever with severe myalgia/arthralgia.\n- Mild skin rash observed.\n\n**Recommended Treatment**\n- Advise aggressive oral rehydration.\n- Paracetamol for fever management.\n\n**Warning Signs**\n- Monitor platelets and hematocrit closely.\n- Watch for signs of bleeding.'
            }
            
        res_ticket = supabase.table('tickets').insert(ticket).execute()
        ticket_id = res_ticket.data[0]['id']
        
        if status in ['approved', 'closed']:
            try:
                supabase.table('orders').insert({'ticket_id': ticket_id}).execute()
            except Exception as e:
                print('Skipping order seeding due to schema error:', e)
            
        time.sleep(0.1)
        
    print('Dengue pandemic seeding complete! Dashboard is now populated with detailed data.')

if __name__ == '__main__':
    seed()

