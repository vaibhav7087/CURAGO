import os
import pandas as pd
import asyncio
from google import genai
from google.genai import types
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Setup Clients
client = genai.Client()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

async def get_embedding(text: str):
    response = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    return response.embeddings[0].values

async def process_and_upload():
    print("🚀 Starting Database Ingestion...")

    # --- 1. PROCESS SYMPTOMS ---
    print("Loading Symptom2Disease.csv...")
    try:
        df_symptoms = pd.read_csv("Symptom2Disease.csv")
        for index, row in df_symptoms.iterrows():
            disease = row['label']
            symptom_desc = row['text']
            
            # Create the Golden Sentence
            content = f"Symptoms of {disease} include: {symptom_desc}."
            
            # Get AI vector
            vector = await get_embedding(content)
            
            # Save to Supabase
            supabase.table("knowledge_base").insert({
                "content": content,
                "metadata": {"type": "symptom", "disease": disease},
                "embedding": vector
            }).execute()
            print(f"✅ Uploaded Symptom {index} for {disease}")
            
    except Exception as e:
        print(f"Error processing Symptoms: {e}")

    # --- 2. PROCESS REMEDIES ---
    print("\nLoading Home Remedies.csv...")
    try:
        df_remedies = pd.read_csv("Home Remedies.csv")
        for index, row in df_remedies.iterrows():
            issue = row['Health Issue']
            remedy = row['Home Remedy']
            
            # Create the Golden Sentence
            content = f"To treat or manage {issue}, a recommended home remedy is: {remedy}."
            
            # Handle the missing Yoga column safely
            if pd.notna(row['Yogasan']):
                content += f" Helpful Yogasan reference: {row['Yogasan']}"
                
            # Get AI vector
            vector = await get_embedding(content)
            
            # Save to Supabase
            supabase.table("knowledge_base").insert({
                "content": content,
                "metadata": {"type": "remedy", "issue": issue},
                "embedding": vector
            }).execute()
            print(f"✅ Uploaded Remedy {index} for {issue}")
            
    except Exception as e:
        print(f"Error processing Remedies: {e}")

    print("\n🎉 All Data Uploaded Successfully! RAG is ready.")

# Run the script
if __name__ == "__main__":
    asyncio.run(process_and_upload())