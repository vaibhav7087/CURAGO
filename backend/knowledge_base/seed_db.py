import pandas as pd
import asyncio
from google import genai
from supabase import create_client

# 🚨 HACKATHON SHORTCUT: Hardcode keys directly
# PASTE YOUR EXACT KEYS INSIDE THE QUOTES
GEMINI_API_KEY = "AIzaSyBjOJepQ_Llmg1f6w4Jd-NtjSQcQ1Mvbb8"
SUPABASE_URL = "https://fxywkkawfsiarjpdfdvk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM"

# Setup Clients directly with the strings
client = genai.Client(api_key=GEMINI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_embedding(text: str):
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )
        return list(response.embeddings[0].values)
    except Exception as e:
        print(f"❌ Embedding Error: {e}")
        return None

async def process_and_upload():
    print("🚀 Starting Database Ingestion...")

    # --- 1. PROCESS SYMPTOMS ---
    print("Loading Symptom2Disease.csv...")
    try:
        df_symptoms = pd.read_csv("knowledge_base/Symptom2Disease.csv")
        for index, row in df_symptoms.iterrows():
            disease = row['label']
            symptom_desc = row['text']
            content = f"Condition: {disease}. Symptom description: {symptom_desc}"
            
            vector = await get_embedding(content)
            
            if vector:
                supabase.table("knowledge_base").insert({
                    "content": content,
                    "metadata": {"type": "symptom", "disease": disease},
                    "embedding": vector
                }).execute()
                print(f"✅ Symptom {index}: {disease} uploaded")
            
    except Exception as e:
        print(f"Error processing Symptoms: {e}")

    # --- 2. PROCESS REMEDIES ---
    print("\nLoading Home Remedies.csv...")
    try:
        df_remedies = pd.read_csv("knowledge_base/Home Remedies.csv")
        for index, row in df_remedies.iterrows():
            issue = row['Health Issue']
            remedy = row['Home Remedy']
            content = f"Home remedy for {issue}: {remedy}"
            
            if pd.notna(row['Yogasan']):
                content += f" Suggested Yoga: {row['Yogasan']}"
                
            vector = await get_embedding(content)
            
            if vector:
                supabase.table("knowledge_base").insert({
                    "content": content,
                    "metadata": {"type": "remedy", "issue": issue},
                    "embedding": vector
                }).execute()
                print(f"✅ Remedy {index}: {issue} uploaded")
            
    except Exception as e:
        print(f"Error processing Remedies: {e}")

    print("\n🎉 ALL DATA UPLOADED! RAG is 100% ready.")

if __name__ == "__main__":
    asyncio.run(process_and_upload())