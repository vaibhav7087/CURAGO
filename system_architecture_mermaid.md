# System Architecture Mermaid Flowchart (Shapes Only, No Color)

Here is the flowchart using only different shapes to differentiate the types of steps (Start/End, Process, Decision, System/Module). You can copy-paste this into GitHub, Notion, or any Markdown viewer.

```mermaid
flowchart TD
    %% Shapes Guide:
    %% ([Pill]) = Start/End
    %% [Rectangle] = Standard Process/Action
    %% {Rhombus} = Decision Point / Menu
    %% [[Double Rectangle]] = Dashboard / Sub-system
    %% [(Cylinder)] = Data/Logistics/Payment System

    %% Nodes
    Start(["PATIENT CALLS HELPLINE (Start)"])
    LangSelect["LANGUAGE SELECTION\n(English / Hindi / Regional)"]
    IVR{"IVR MENU\n(Triage)"}

    Emergency{"1. EMERGENCY"}
    HumanDoc(["HUMAN DOCTOR\n(Priority End)"])

    GenHealth["2. GENERAL HEALTH"]
    AIAgent["AI VOICE AGENT\n(Dograh + Sarvam + NIM)"]
    CrossExamine["CROSS EXAMINE\n& SUMMARY"]
    
    TraineeDash[["TRAINEE DASHBOARD\n(Review)"]]
    DoctorDash[["DOCTOR DASHBOARD\n(Review)"]]

    FollowUp["3. FOLLOW UP"]
    StatusCheck["STATUS CHECK"]

    %% Doctor Actions
    Approve["APPROVE\n(One-Click)"]
    EditPresc["EDIT PRESCRIPTION"]
    DocCallback["DOCTOR CALL BACK"]

    %% Logistics
    Payments[("CONFIRMATION & PAYMENTS\n(Pre-paid, Post-paid, etc.)")]
    Dispatch["DISPATCH TO WAREHOUSE"]
    Inventory[("L1: VILLAGE (Common)\nL2: CLUSTER (Specific/Cold)\nL3: DISTRICT (Rare)")]
    Delivery["DELIVERY SLOTS\n(Morning/Night)"]
    PatientMeds["PATIENT RECEIVES MEDS"]

    %% Post-Delivery Follow Up
    AutoCall["AUTOMATED FOLLOW-UP CALL"]
    Resolved{"RESOLVED?"}
    CaseClosed(["CASE CLOSED\n(End)"])

    TraineeVisit["TRAINEE HOME VISIT\n(Shift-based)"]
    DocReassess["DOCTOR RE-ASSESSMENT"]

    Persists{"CONDITION PERSISTS?"}
    CampPool["SPECIALIST CAMP POOL"]
    SpecialistCamp(["WEEKLY SPECIALIST CAMP\n(End)"])

    %% Edges / Connections
    Start --> LangSelect
    LangSelect --> IVR

    %% Branch 1: Emergency
    IVR --> Emergency
    Emergency --> HumanDoc

    %% Branch 2: General Health
    IVR --> GenHealth
    GenHealth --> AIAgent
    AIAgent --> CrossExamine
    CrossExamine --> TraineeDash
    CrossExamine --> DoctorDash

    %% Branch 3: Follow Up
    IVR --> FollowUp
    FollowUp --> StatusCheck

    %% Doctor Actions to Payments
    DoctorDash --> Approve
    DoctorDash --> EditPresc
    DoctorDash --> DocCallback

    Approve --> Payments
    EditPresc --> Payments

    %% Logistics Flow
    Payments --> Dispatch
    Dispatch --> Inventory
    Inventory --> Delivery
    Delivery --> PatientMeds
    PatientMeds --> AutoCall

    %% Resolution Flow
    AutoCall --> Resolved
    Resolved -- YES --> CaseClosed
    Resolved -- NO --> TraineeVisit
    Resolved -- NO --> DocReassess

    TraineeVisit --> Persists
    DocReassess --> Persists

    Persists -- NO --> CaseClosed
    Persists -- YES --> CampPool
    CampPool --> SpecialistCamp
```
