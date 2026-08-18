# Hackathon Handbook: Prerequisite Setup

Complete these manual steps in a browser before running the main application stack.

---

### 1. Supabase (Database)
1. Go to https://supabase.com → Sign Up (new account if old one is paused).
2. Create a new project. Name: `curago-v2`. Region: pick closest (Mumbai if available).
3. Wait for project to provision (~2 min).
4. Go to **SQL Editor** → Paste the entire contents of `curago/setup_supabase.sql` → Click **Run**.
5. Go to **Settings → API** → Copy:
   - `Project URL` (e.g., `https://xxxxx.supabase.co`)
   - `anon public` key (starts with `eyJ...`)
6. Save these two values. You will paste them into `.env` files later.

---

### 2. NVIDIA NIM (Primary LLM)
1. Go to https://build.nvidia.com → Sign Up / Log In with NVIDIA account.
2. Browse to any model (e.g., `meta/llama-3.1-70b-instruct`).
3. Click **"Get API Key"** → Copy the key (starts with `nvapi-...`).
4. *Free tier: 40 requests/minute, no credit card.*

---

### 3. Groq (Fallback LLM)
1. Go to https://console.groq.com → Sign Up.
2. Go to **API Keys** → Create new key → Copy.
3. *Free tier: 30 requests/minute, no credit card.*

---

### 4. Sarvam AI (Indian Language STT/TTS)
1. Go to https://www.sarvam.ai → Sign Up.
2. Go to **Dashboard → API Keys** → Copy the API key.
3. *₹100 free credits on signup. No credit card.*

---

### 5. Twilio (Telephony + SMS)
1. Go to https://www.twilio.com/try-twilio → Sign Up (verify with your phone).
2. You get a free **US (+1) phone number** automatically.
3. Go to **Phone Numbers → Verified Caller IDs** → Add your Indian Jio number (the one you'll call from during the demo).
4. Copy from the Console:
   - `Account SID` (starts with `AC...`)
   - `Auth Token`
   - `Twilio Phone Number` (the US number, e.g., `+1234567890`)
5. *Important: Twilio trial SMS will prepend "Sent from your Twilio trial account" to all outbound messages. This is cosmetic only.*

---

### 6. Google AI (Gemini Embeddings for RAG)
1. Go to https://aistudio.google.com/apikey → Create API Key → Copy.
2. *Free tier. This is used ONLY for generating embeddings (768 dims).*

---

### 7. Dograh (Voice Orchestrator)
1. Open PowerShell in `curago/dograh_setup/`.
2. Run:
   ```powershell
   Invoke-WebRequest -OutFile docker-compose.yaml https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml
   Invoke-WebRequest -OutFile start_docker.ps1 https://raw.githubusercontent.com/dograh-hq/dograh/main/scripts/start_docker.ps1
   .\start_docker.ps1
   ```
3. Wait ~2-3 min for images to download. Dograh UI will be at `http://localhost:3010`.
4. In the Dograh UI:
   - Go to **Settings → Integrations**.
   - Add **Twilio** provider: paste Account SID, Auth Token, Phone Number.
   - Add **Sarvam AI** provider: paste API Key.
   - Add a **Custom OpenAI-Compatible** LLM provider:
     - Name: `nvidia-nim`
     - Base URL: `https://integrate.api.nvidia.com/v1`
     - API Key: your NIM key
     - Model: `meta/llama-3.1-70b-instruct`

---

### 8. Jio ISD Pack (For calling the Twilio US Number)
To call your Twilio US number from India without massive charges during the demo, you need an ISD pack.

**Plan Details:**
- **Cost:** ₹39
- **Talktime:** 30 Minutes of calling to USA/Canada
- **Validity:** 7 Days

**How to activate:**
1. Open **MyJio App**.
2. Go to Recharge → Scroll tabs to **ISD**.
3. Select the **"₹39 Global ISD Pack"** and pay.
4. Your Indian number can now call your Twilio `+1` number.
