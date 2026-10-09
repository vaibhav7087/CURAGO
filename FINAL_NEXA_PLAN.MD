# FINAL_NEXA_PLAN — Curago Nexathon 2026 (Project Competition, Healthcare)

> **Status:** LOCKED. Decisions confirmed by owner. Opencode executes everything; owner approves only.
> **Budget:** 4 hours (H0–H4). **Demo:** 8 minutes, one ticket, no mocks.
> **Deck:** `docs/Curago_Nexathon.pptx` (12 slides, built + QA-passed) — submit ASAP, execution follows.

---

## 0. Locked decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Outbound messaging (dead Twilio creds in `.env`, expired Meta token in `whatsapp.py:7`) | **Log-only mode** — `NOTIFY_SMS/WHATSAPP` flags OFF, flows return `sms_sent:false`, zero network calls on stage |
| 2 | Triage data | **Attempt real** on `knowledge_base/Symptom2Disease.csv` (1201 rows); **synthetic default** on stage via `DS_DATA_MODE=real\|synthetic` flag + `demo_cache` fallback |
| 3 | Adaptive recommendation | **Full loop via isolated subagent in parallel**; merge only if it beats v0 on replay + review — else ship hardcoded rules+kNN labeled adaptive (same endpoint + card contract, zero main-track risk) |

## 1. Code truth (from code, not docs — verified by grep/read)

- **Voice = Vapi only.** `backend/app/routers/webhook.py:111-157` parses 3 payload shapes (Vapi end-of-call-report, Dograh-style, generic). Zero `sarvam` strings in backend. No Twilio voice. Mid-call live paths: `POST /api/rag/search` (Gemini embed → `match_documents`, thr 0.4, top-5) + `POST /api/vapi-tool` history. Post-call only: transcript + `analysis.structuredData` + caller + call ID. No audio, no per-turn control.
- **No-Twilio is failure-safe but slow:** `services/sms.py:13-15` returns `False` without creds — but `.env` HAS creds, so every Approve/Delivered attempts a real call that fails. `doctor.py:51` and `orders.py:41-44` never raise on failure (bool return). WhatsApp token hardcoded, certainly expired.
- **Doctor UI bypasses backend:** `DoctorDashboard.jsx:299-317,351-368` writes `status:'approved'` + inserts orders direct to Supabase. Backend `/approve` writes `'resolved'` + SMS. Two vocabularies — normalize on READ, never rewrite writes.
- **Two vitals paths compete:** web trainee → dumb `PATCH /api/trainee/{id}/vitals` (`trainee.py:32` — overwrites, no merge/AI); Flutter → rich `POST /api/tickets/vitals/{id}` (`vitals.py:19` — merge + 2-stage Groq AI → `doctor_review`). Demo vitals on the Flutter path only.
- **Empty tables = empty demo:** `inventory` (0), `camps` (0), `knowledge_base` (0). Live counts today: patients 21 / tickets 21 / orders 5.
- **Webhook ticket insert waits on synchronous Groq extraction** (`webhook.py:174`) — Groq key exists, keep; DS `predict_severity` is local/fast.
- **Flutter** `config.dart:4` points at onrender (cold starts) — keep backend awake via ping for stage.
- **DS today:** `ds/predict.py` (`predict_severity` + `detect_outbreaks_statistical`), `POST /api/predict-severity`, `GET /api/analytics/enhanced`, webhook DS merge, dashboard cards. `triage.pkl` = synthetic NHAMCS-like (placeholder). Tests: pytest 21/21, Playwright 3 pass/1 skip, `npm run build` ~5s.

---

## 2. H0–H1 — Safety + demo hardening (demo cannot die)

### Step 0.1 — Notify kill-switch (log-only mode)
- **Files:** `backend/app/services/sms.py`, `backend/app/services/whatsapp.py`
- **Change:** top-of-function guard: `if os.getenv("NOTIFY_SMS","0") != "1": print("[demo] SMS suppressed"); return False` (same for WhatsApp with `NOTIFY_WHATSAPP`). No signature changes; callers (`doctor.py:51`, `orders.py:41-44`) untouched.
- **Accept:** pull network cable → Approve + Delivered return 200s, logs show suppression, no hangs.

### Step 0.2 — Status normalization (read path only)
- **File:** `backend/app/routers/analytics.py` (`/enhanced` + `/outbreaks` if touched)
- **Change:** count `approved` together with `resolved` for fulfillment/resolution metrics. Do NOT alter any write path.
- **Accept:** seeded approved tickets appear in fulfilled counts.

### Step 0.3 — Seed demo data (Supabase SQL)
- **Rows:** 5 `inventory` matching UI m1–m5 (Paracetamol 500mg, Amoxicillin 250mg, Ibuprofen 400mg, Ceftriaxone Inj 1g, ORS Packets; L1/L2 `center_id`, stock>0); 2–3 `camps` (Eye Care, Diabetes, Cardio); 12–15 `knowledge_base` rows from `knowledge_base/Home Remedies.csv` via existing `seed_db.py` pattern (Gemini embeddings).
- **Accept:** `GET /api/inventory` ≥5 rows; `GET /api/camps` ≥2; `POST /api/rag/search {"query":"fever"}` returns ≥1 result; dashboard dropdowns non-empty.

---

## 3. H1–H2 — Triage: real attempt, synthetic default

### Step 1.1 — `ds/train_disease.py` (new, mirrors `train_triage.py` structure)
- **Data:** `knowledge_base/Symptom2Disease.csv` (label,text) → clean (lower/strip), stratified 80/20 split.
- **Models:** TF-IDF (1–2gram) + LogisticRegression (balanced) vs LinearSVC (calibrated). Report accuracy, F1-macro, top-3 accuracy, per-class PR on overlapping symptoms, confusion matrix PNG, latency ms, model MB (<5MB, CPU-only, offline).
- **Outputs:** `ds/models/disease_clf.joblib`, `disease_metrics.csv`, `disease_confusion.png`.

### Step 1.2 — Global data flag
- **Mechanism:** `DS_DATA_MODE` env (`real|synthetic`, default `synthetic`) read in `ds/predict.py`; `POST /api/predict-severity` response includes `data_mode`. Dashboard card shows tiny badge. `ds/demo_cache/` remains the offline fallback.
- **Rule:** synthetic only for load tests/cold-start; every metric table carries a `Data Source` column (n + provenance). Real run ships in PPT appendix either way.
- **Accept:** flip flag → endpoint switches model; default path serves current `triage.pkl` numbers (AUC 0.96) on stage.

---

## 4. H2–H3.5 — Main track + adaptive subagent (parallel, shared contract)

### Shared contract (main track builds, subagent fills — no breaking changes)
- `POST /api/recommend {ticket_id}` → `{suggestions:[{medicine, dose, why}], model:"v0-rules"|"bandit-v1", abstain:bool}`
- Dashboard card: suggestion list + Accept / Edit / Reject + "Why this?" expander.
- Implicit logging from day one: approvals already persist via `orders.package_items` (no new table for v0).

### Step 2.1 — Main track: v0 brain + card (~45 min)
- Candidates = union of (a) curated disease→standard-meds map (~30 entries from `Symptom2Disease` labels), (b) kNN over past approved tickets (embedding of `symptoms_summary`), (c) current LLM suggestion — **all filtered to `inventory.stock > 0`**, dose sanity, abstain if confidence < 0.60.
- Card wired in `DoctorDashboard.jsx` next to DS severity card. `POST /api/recommend` + `ds/recommender.py`.
- **Accept:** offline, <200ms, empty-stock meds never suggested, abstain path renders.

### Step 2.2 — Subagent (isolated Task): full adaptive loop
- Scope: `rx_feedback(ticket_id, suggested[], approved[], reward)` migration (reward: accept 1.0 / edit 0.5 / reject 0.0); LinUCB-per-symptom-cluster reweight script (`ds/train_bandit.py`, nightly batch, never per-click); acceptance-rate eval on replay of real approvals; DDI guard table for the ~15 formulary drugs (hand-authored, fails closed).
- **Merge gate (all must hold):** beats v0 on replay acceptance + `pytest` green + review of `rx_feedback` writes. Else discard, ship v0. Main track never blocks.

---

## 5. H3.5–H4 — Prove it (pre-Vapi gate = Vapi goes last)

Run in order; Vapi test call ONLY after all green:
1. `curl /health` → `{"status":"ok"}`; Supabase ping (6 tables reachable)
2. `triage.pkl` loads 10/10; `demo_cache/*.json` exist; seeds present (Step 0.3 counts)
3. `py -3.11 -m pytest tests/test_ds.py tests/test_integration.py -q` → 21/21 (record output for PPT)
4. `npm run test:e2e` (Playwright) + `npm run build` clean
5. Backend cold-boot timed; Render pinged awake; Flutter `baseUrl` confirmed reachable
6. Export into `docs/ppt_assets/`: `metric_table.csv`, `shap_summary.png`, `demand_forecast_comparison.png`, disease metrics, acceptance-trend stub

---

## 6. 8-minute demo script (one ticket, no mocks)

| T | Beat |
|---|---|
| 0:00 | Hindi call to Vapi helpline (live audio) |
| 2:00 | Ticket + DS severity + audit banner appear on dashboard |
| 3:30 | Doctor prescribes from adaptive suggestions, Approve & Dispatch → order created |
| 5:00 | Flutter delivery: accept → navigate → delivered (UPI/Cash) |
| 6:30 | Trainee vitals → AI follow-ups → `doctor_review` |
| 7:30 | Analytics: outbreak alert + metrics + offline fallback shown |

## 7. Rollback

- Pre-DS checkpoint: commit `55b6c88` (`git reset --hard 55b6c88` restores; phase commits after each H-block).
- Notify flags default OFF — re-enable with env, no code change.
- `DS_DATA_MODE=synthetic` default — real model never risks the stage.

## 8. PPT mapping (`docs/Curago_Nexathon.pptx`, 12 slides, submitted)

Slides 1–4 problem/loop/architecture → 5 Vapi-only honesty + log-only → 6 live counts → 7 ML metrics + flag → 8 adaptive v0 + bandit Phase-2 → 9 second reader → 10 testing gate → 11 demo script → 12 roadmap. Appendix: real-data triage run, replay eval, IDSP/Dograh future work.
