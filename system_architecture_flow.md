# System Architecture & Patient Flow
*(Based on the NaN-Chalant Telemedicine Architecture Diagram)*

This document outlines the end-to-end operational flow of the telemedicine system, from the initial patient call to final resolution and potential escalation. It represents a full healthcare logistics and triage supply chain, extending far beyond the initial AI interaction.

---

## Phase 1: Intake & Triage (The Front Door)

1. **Patient Calls Helpline (Start):** The journey begins when a patient dials the designated Twilio/telephony number.
2. **Language Selection:** An IVR (Interactive Voice Response) system prompts the user to select their preferred language (e.g., English, Hindi, or Regional).
3. **IVR Menu (Triage Routing):**
   - **Path 1: Emergency:** If the patient selects emergency, the system bypasses AI and routes the call directly to a Human Doctor (Priority).
   - **Path 3: Follow Up:** Patients calling to check on existing cases are routed to a "Status Check" module.
   - **Path 2: General Health:** Standard health inquiries are routed to the **AI Voice Agent** (powered by Dograh/NIM in V2).

4. **The AI Agent (Cross-Examine & Summary):** 
   - The AI acts as the first line of defense. It cross-examines the patient to understand their symptoms, duration, and severity.
   - It synthesizes this conversation into a structured summary (a "ticket") for human review.

---

## Phase 2: Human Review (The Dashboards)

1. **Dashboard Distribution:** The AI's structured summary is immediately pushed to two interfaces:
   - **Trainee Dashboard (Review)**
   - **Doctor Dashboard (Review)**
2. **Doctor Action:** The human doctor reviews the AI's triage assessment and has three primary options:
   - **Approve (One-Click):** If the AI's assessment and proposed medication look correct, the doctor approves it instantly.
   - **Edit Prescription:** The doctor modifies the medication or dosage before approving.
   - **Doctor Call Back:** If the AI missed crucial context or the case is complex, the doctor manually calls the patient back.

---

## Phase 3: Commerce & Logistics (The Supply Chain)

1. **Confirmation & Payments:** Once a prescription is approved, the payment gateway is triggered. Options are tailored for rural realities:
   - *Payment Types:* Pre-loaded Card, Online Payment, Monthly Collection.
   - *Fulfillment:* Take away, Pre-paid, Post-paid.
2. **Dispatch to Warehouse & Inventory Routing:** The prescription is dispatched to a fulfillment center. Meds are sourced based on a tiered inventory system:
   - **L1 (Village):** Common medicines readily available locally.
   - **L2 (Cluster):** Specific medicines or those requiring cold storage.
   - **L3 (District):** Rare or specialized medications.
3. **Delivery:** Medicines are dispatched during specific Delivery Slots (Morning/Night).
4. **Patient Receives Meds:** The physical supply chain completes when the patient receives their prescription.

---

## Phase 4: Resolution & Escalation (The Safety Net)

1. **Automated Follow-up Call:** After a set period, the system automatically calls the patient to check on their recovery.
2. **Condition Resolved?**
   - **YES:** The case is officially closed (End).
   - **NO:** The system escalates the case to physical intervention.
3. **Physical Intervention:**
   - **Trainee Home Visit:** A shift-based trainee visits the patient's home.
   - **Doctor Re-assessment:** A remote doctor reviews the case again.
4. **Condition Persists?**
   - **NO (resolved after intervention):** Case Closed (End).
   - **YES (chronic or unresolvable at home):** The patient is added to the **Specialist Camp Pool**.
5. **Final Escalation:** The patient is referred to a physical **Weekly Specialist Camp** (End of the digital flow).

---

### Implementation Scope (V2 Hackathon Focus)
The V2 technical stack (Twilio + Dograh + NIM + Supabase + Flutter) covers all 4 phases: **Phase 1** (AI Voice Agent), **Phase 2** (Realtime Dashboards), **Phase 3** (LastMileAgent Delivery), and **Phase 4** (Automated Follow-up SMS).
