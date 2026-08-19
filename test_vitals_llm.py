import sys, os, json
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
from app.services.llm import groq_client

prompt = """
You are an expert AI doctor assisting a field trainee. 
Patient Symptoms reported over phone: ['cold']
Vitals recorded physically by trainee: {"temperature": "102.5", "blood_pressure": "135/85", "spo2": "96", "extra_notes": "Throat is extremely red and swollen"}

Analyze this combined data. 
If this is the FIRST time you are seeing this data (no 'extra_notes' provided), and you need the trainee to perform specific additional physical checks (e.g., 'Check eyes for yellowness', 'Palpate stomach'), return a JSON object with:
{"status": "needs_more_checks", "requested_checks": ["Check X", "Check Y"]}

CRITICAL RULE: If the trainee HAS provided 'extra_notes' in the vitals data, it means they just completed your requested checks. You MUST NOT ask for more checks. You MUST return a JSON object with:
{"status": "complete", "advanced_diagnosis": "Your detailed differential diagnosis based on ALL data including the extra notes..."}

Return ONLY valid JSON. No markdown formatting.
"""

response = groq_client.chat.completions.create(
    model='llama3-70b-8192',
    messages=[{'role': 'user', 'content': prompt}],
    timeout=15
)
content = response.choices[0].message.content
print('RAW RESPONSE:')
print(content)
print('CLEANED:')
cleaned_content = content.replace('```json', '').replace('```', '').strip()
print(cleaned_content)
try:
    print(json.loads(cleaned_content))
except Exception as e:
    print('JSON ERROR:', e)
