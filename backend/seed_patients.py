import os
import sys
import uuid
import random
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv(".env")

from app.core.database import supabase

def seed():
    print("Seeding 7 patients and tickets...")
    
    patients = [
        {"name": "Anil Gupta", "phone_number": "919999999991", "village": "Rampur", "age": 45, "gender": "Male"},
        {"name": "Sunita Sharma", "phone_number": "919999999992", "village": "Dharampur", "age": 34, "gender": "Female"},
        {"name": "Ravi Kumar", "phone_number": "919999999993", "village": "Sitapur", "age": 52, "gender": "Male"},
        {"name": "Meena Devi", "phone_number": "919999999994", "village": "Rampur", "age": 28, "gender": "Female"},
        {"name": "Suresh Patel", "phone_number": "919999999995", "village": "Madhopur", "age": 60, "gender": "Male"},
        {"name": "Kamala Bai", "phone_number": "919999999996", "village": "Dharampur", "age": 42, "gender": "Female"},
        {"name": "Rajesh Singh", "phone_number": "919999999997", "village": "Sitapur", "age": 39, "gender": "Male"},
    ]
    
    symptoms_list = [
        "High fever, dry cough, body ache",
        "Severe stomach pain and nausea after eating",
        "Persistent headache and dizziness",
        "Chest tightness and shortness of breath",
        "Skin rash and itching on arms",
        "Joint pain and swelling in knees",
        "Sore throat and difficulty swallowing"
    ]
    
    # 1. Insert patients
    for i, p in enumerate(patients):
        res = supabase.table("patients").insert(p).execute()
        patient_id = res.data[0]["id"]
        
        # 2. Insert ticket for each patient
        ticket = {
            "patient_id": patient_id,
            "symptoms_summary": symptoms_list[i],
            "severity": random.choice(["Low", "Medium", "High"]),
            "status": "open",
            "vitals_data": {}
        }
        supabase.table("tickets").insert(ticket).execute()
        
    print("Seeding complete!")

if __name__ == "__main__":
    seed()
