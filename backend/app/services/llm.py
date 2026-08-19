import os
from google import genai
from google.genai import types
from app.core.database import supabase
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

# Gemini for Embeddings ONLY (RAG search)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE" else None

# NIM and Groq for Chat/Extraction (Primary and Fallback)
NIM_KEY = os.getenv("NVIDIA_NIM_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

nim_client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NIM_KEY) if NIM_KEY else None
groq_client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY) if GROQ_KEY else None

async def get_embedding(text: str) -> list[float]:
    """Converts text into a 768-dim vector using Gemini."""
    if not gemini_client:
        print("Warning: No valid Gemini API Key found for embeddings.")
        return []
    try:
        response = gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        return list(response.embeddings[0].values)
    except Exception as e:
        print(f"Embedding Error: {e}")
        return []

async def search_medical_knowledge(user_query: str) -> list:
    """Searches Supabase for the closest matching medical guidelines."""
    try:
        # Bias the search toward remedies
        search_phrase = f"Home remedy and treatment for {user_query}. Skip symptoms, find remedies."
        
        query_vector = await get_embedding(search_phrase)
        if not query_vector:
            return [{"content": "Error generating search vector.", "similarity": 0}]

        rpc_resp = supabase.rpc("match_documents", {
            "query_embedding": query_vector,
            "match_threshold": 0.4,
            "match_count": 5
        }).execute()

        if not rpc_resp.data:
            return [{"content": "No specific medical guidelines found in the database.", "similarity": 0}]
        
        return rpc_resp.data

    except Exception as e:
        print(f"RAG Search Error: {e}")
        return [{"content": "Error retrieving medical guidelines from the database.", "similarity": 0}]

def extract_patient_data(transcript: str) -> dict:
    """Uses NIM (or Groq fallback) to extract patient info from transcript."""
    prompt = [
        {"role": "system", "content": "You are a medical data extractor. Extract the patient's name, severity (High, Medium, Low), symptoms, age, gender, and village from the transcript. Also, based on the symptoms, suggest a list of medicines from this available inventory: [Paracetamol 500mg, Amoxicillin 250mg, Ibuprofen 400mg, Ceftriaxone Inj 1g, ORS Packets]. IMPORTANT: You MUST translate all extracted data into English before returning the JSON, regardless of the language spoken in the transcript. Return ONLY a valid JSON object with keys: patient_name, severity, symptoms, age, gender, village, suggested_medicines (array of strings). If a value is unknown, use null. Do not include markdown formatting."},
        {"role": "user", "content": transcript}
    ]
    
    response_content = ""
    try:
        # 1. Primary: Try Groq with the verified model
        if groq_client:
            print("Attempting extraction with Groq (openai/gpt-oss-20b)...")
            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=prompt,
                max_tokens=1024,
                temperature=0.2
            )
            response_content = response.choices[0].message.content
        else:
            raise Exception("Groq not configured")
    except Exception as e:
        print(f"Extraction failed with Groq: {e}. Falling back to Gemini...")
        try:
            if gemini_client:
                print("Attempting extraction with Gemini fallback...")
                prompt_str = prompt[0]["content"] + "\n\nTranscript:\n" + prompt[1]["content"]
                response = gemini_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt_str
                )
                response_content = response.text
            else:
                raise Exception("No fallback LLM available")
        except Exception as fallback_e:
            print(f"Fallback extraction failed: {fallback_e}")
            return {}

    # Clean the response to ensure it's valid JSON
    cleaned_content = response_content.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(cleaned_content)
    except Exception as e:
        print(f"JSON Parse Error: {e}\nRaw content: {response_content}")
        return {}