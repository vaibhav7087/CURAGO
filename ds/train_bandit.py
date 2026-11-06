"""
ds/train_bandit.py -- LinUCB-per-symptom-cluster reweight for the prescribing recommender.

Offline only: reads rx_feedback rows from a JSON file (or --demo in-memory
sample rows), NEVER touches live Supabase. Zero rows -> priors-only output,
never crashes.

Row format (liberal; any of these shapes accepted):
  {"ticket_id": str|None, "symptoms": str, "disease": str|None,
   "suggested": ["Paracetamol 500mg", ...] | [{"medicine": ...}, ...],
   "approved":  [...] (same shapes; mirrors orders.package_items),
   "reward": 1.0 | 0.5 | 0.0 (optional; derived if absent)}

Reward rubric (matches setup_rx_feedback.sql):
  accept-as-is -> 1.0 | edited (partial overlap) -> 0.5 | rejected -> 0.0

Method: per symptom-cluster, per formulary-arm LinUCB (Ridge, d=8, CPU/numpy
only). Context x = [bias, len_norm, age_norm, n_sugg_norm, kw_fever,
kw_pain, kw_gi, kw_resp]. Update per shown arm: kept -> row reward,
dropped -> 0.0; doctor-added arms (never shown) get no update. Output is
per-cluster normalized arm weights + epsilon-greedy config for serving.

Usage:
  py -3.11 ds/train_bandit.py                                  # empty -> priors-only
  py -3.11 ds/train_bandit.py --input rows.json
  py -3.11 ds/train_bandit.py --demo                           # 12 built-in sample rows
  py -3.11 ds/train_bandit.py --demo --output ds/models/bandit_weights.json
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Formulary arms: must match FORMULARY_DOSE keys in ds/recommender.py (read-only mirror).
ARMS = [
    "Paracetamol 500mg",
    "Amoxicillin 250mg",
    "Ibuprofen 400mg",
    "Ceftriaxone Inj 1g",
    "ORS Packets",
]

# Symptom-cluster keyword map. First match in priority order wins, else "other".
CLUSTER_KEYWORDS = {
    "fever": ("fever", "temperature", "chills", "dengue", "malaria", "typhoid"),
    "pain": ("pain", "headache", "migraine", "joint", "arthritis", "back",
             "cervical", "spondylosis", "hemorrhoid", "varicose"),
    "respiratory": ("cough", "cold", "breath", "asthma", "pneumonia", "chest"),
    "gi": ("diarrh", "vomit", "stool", "loose motion", "ulcer", "reflux",
           "jaundice", "stomach", "abdomen", "gastro"),
    "skin": ("rash", "itch", "acne", "psoriasis", "chicken pox", "impetigo",
             "fungal", "lesion", "boil"),
    "urinary": ("urin", "uti", "burning micturition", "dysuria"),
}
CLUSTERS = list(CLUSTER_KEYWORDS) + ["other"]

DIM = 8          # context dimension (see module docstring for layout)
ALPHA = 1.0      # LinUCB exploration bonus coefficient
LAMBDA = 1.0     # ridge prior (A init = LAMBDA * I)

EPSILON_CFG = {
    "epsilon": 0.15,        # explore fraction at serving time
    "epsilon_decay": 0.999,  # per-day multiplier (applied by server, not here)
    "min_epsilon": 0.05,
    "alpha": ALPHA,         # UCB bonus kept alongside epsilon-greedy
}


def cluster_for(symptoms: str, disease: str = "") -> str:
    text = f"{symptoms or ''} {disease or ''}".lower()
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        if any(k in text for k in keywords):
            return cluster
    return "other"


def med_names(items) -> list:
    """Normalize suggested/approved JSONB to a list of medicine-name strings."""
    if items is None:
        return []
    if isinstance(items, dict):  # e.g. {"suggestions": [...]}
        for key in ("suggestions", "items", "medicines", "package_items"):
            if isinstance(items.get(key), list):
                return med_names(items[key])
        return []
    if isinstance(items, str):
        return [items] if items in ARMS else []
    names = []
    for it in items:
        if isinstance(it, str):
            names.append(it)
        elif isinstance(it, dict):
            for key in ("medicine", "name", "medicine_name"):
                if it.get(key):
                    names.append(str(it[key]))
                    break
    return names


def derive_reward(suggested: list, approved: list) -> float:
    """Fallback rubric when a row has no explicit reward."""
    s, a = set(suggested), set(approved)
    if not a:
        return 0.0
    if a == s:
        return 1.0
    return 0.5


def context_for(row: dict, n_suggested: int) -> np.ndarray:
    text = f"{row.get('symptoms') or ''} {row.get('disease') or ''}".lower()
    age = row.get("age")
    try:
        age_norm = min(max(float(age), 0.0), 100.0) / 100.0
    except (TypeError, ValueError):
        age_norm = 0.0
    return np.array([
        1.0,
        min(len(text) / 200.0, 1.0),
        age_norm,
        min(n_suggested / 5.0, 1.0),
        1.0 if any(k in text for k in CLUSTER_KEYWORDS["fever"]) else 0.0,
        1.0 if any(k in text for k in CLUSTER_KEYWORDS["pain"]) else 0.0,
        1.0 if any(k in text for k in CLUSTER_KEYWORDS["gi"]) else 0.0,
        1.0 if any(k in text for k in CLUSTER_KEYWORDS["respiratory"]) else 0.0,
    ], dtype=float)


def load_rows(input_path: str | None) -> list:
    """Load feedback rows from JSON file; missing/empty -> [] (never raises)."""
    candidates = []
    if input_path:
        candidates.append(Path(input_path))
    env_path = os.getenv("RX_FEEDBACK_JSON")
    if env_path:
        candidates.append(Path(env_path))
    # Repo-convention export path (optional; offline file, not a live DB read).
    candidates.append(Path(__file__).parent / "data" / "rx_feedback_export.json")
    for path in candidates:
        if path and path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):  # allow {"rows": [...]} wrapper
                    data = data.get("rows", [])
                rows = [r for r in (data or []) if isinstance(r, dict)]
                print(f"Loaded {len(rows)} rows from {path}")
                return rows
            except Exception as e:  # corrupt file -> treat as empty, don't crash
                print(f"Warning: could not parse {path} ({e}); using empty input.")
                return []
    print("No input file found; using empty input (priors-only output).")
    return []


def demo_rows() -> list:
    """12 file-free sample rows spanning clusters x accept/edit/reject."""
    return [
        {"symptoms": "high fever with chills for 3 days", "disease": "Dengue",
         "suggested": ["Paracetamol 500mg", "ORS Packets"],
         "approved": ["Paracetamol 500mg", "ORS Packets"], "reward": 1.0},
        {"symptoms": "fever and body ache", "disease": "Common Cold",
         "suggested": ["Paracetamol 500mg", "ORS Packets"],
         "approved": ["Paracetamol 500mg", "ORS Packets"], "reward": 1.0},
        {"symptoms": "fever with loose stools", "disease": "Typhoid",
         "suggested": ["Paracetamol 500mg", "Amoxicillin 250mg", "ORS Packets"],
         "approved": ["Paracetamol 500mg", "ORS Packets"], "reward": 0.5},
        {"symptoms": "severe headache, nausea in sunlight", "disease": "Migraine",
         "suggested": ["Paracetamol 500mg", "Ibuprofen 400mg"],
         "approved": ["Paracetamol 500mg", "Ibuprofen 400mg"], "reward": 1.0},
        {"symptoms": "knee joint pain for months", "disease": "Arthritis",
         "suggested": ["Ibuprofen 400mg", "Paracetamol 500mg"],
         "approved": ["Ibuprofen 400mg"], "reward": 0.5},
        {"symptoms": "dry cough and breathing difficulty", "disease": "Bronchial Asthma",
         "suggested": ["Paracetamol 500mg"], "approved": [], "reward": 0.0},
        {"symptoms": "cough with fever and chest pain", "disease": "Pneumonia",
         "suggested": ["Paracetamol 500mg", "Amoxicillin 250mg"],
         "approved": ["Paracetamol 500mg", "Amoxicillin 250mg"], "reward": 1.0},
        {"symptoms": "watery diarrhoea since morning", "disease": "Jaundice",
         "suggested": ["ORS Packets", "Paracetamol 500mg"],
         "approved": ["ORS Packets", "Paracetamol 500mg"], "reward": 1.0},
        {"symptoms": "burning stomach pain after food", "disease": "peptic ulcer disease",
         "suggested": ["Paracetamol 500mg", "ORS Packets"],
         "approved": ["Paracetamol 500mg"], "reward": 0.5},
        {"symptoms": "itchy red rash on arms", "disease": "Fungal infection",
         "suggested": ["Paracetamol 500mg"], "approved": [], "reward": 0.0},
        {"symptoms": "burning while urinating", "disease": "urinary tract infection",
         "suggested": ["Amoxicillin 250mg", "ORS Packets"],
         "approved": ["Amoxicillin 250mg", "ORS Packets"], "reward": 1.0},
        {"symptoms": "general weakness, no clear symptom", "disease": "Hypertension",
         "suggested": ["Paracetamol 500mg"],
         "approved": ["Paracetamol 500mg"], "reward": 1.0},
    ]


def train(rows: list) -> dict:
    """LinUCB fit per (cluster, arm). Empty rows -> uniform priors."""
    state = {c: {a: {"A": np.eye(DIM) * LAMBDA, "b": np.zeros(DIM),
                     "n": 0, "reward_sum": 0.0} for a in ARMS} for c in CLUSTERS}
    ctx_sum = {c: np.zeros(DIM) for c in CLUSTERS}
    ctx_n = {c: 0 for c in CLUSTERS}
    n_used = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        suggested = [m for m in med_names(row.get("suggested")) if m in ARMS]
        approved = [m for m in med_names(row.get("approved")) if m in ARMS]
        if not suggested:
            continue  # nothing was shown -> no bandit update
        raw = row.get("reward")
        try:
            reward = float(raw) if raw is not None else derive_reward(suggested, approved)
        except (TypeError, ValueError):
            reward = derive_reward(suggested, approved)
        reward = min(max(reward, 0.0), 1.0)
        cluster = cluster_for(str(row.get("symptoms") or ""), str(row.get("disease") or ""))
        x = context_for(row, len(suggested))
        kept = set(suggested) & set(approved)
        for arm in suggested:
            st = state[cluster][arm]
            arm_reward = reward if arm in kept else 0.0
            st["A"] += np.outer(x, x)
            st["b"] += arm_reward * x
            st["n"] += 1
            st["reward_sum"] += arm_reward
        ctx_sum[cluster] += x
        ctx_n[cluster] += 1
        n_used += 1

    clusters_out = {}
    for cluster in CLUSTERS:
        x_bar = ctx_sum[cluster] / ctx_n[cluster] if ctx_n[cluster] else np.array(
            [1.0] + [0.0] * (DIM - 1))
        scores, counts, mean_rewards = {}, {}, {}
        for arm in ARMS:
            st = state[cluster][arm]
            counts[arm] = st["n"]
            mean_rewards[arm] = round(st["reward_sum"] / st["n"], 4) if st["n"] else 0.0
            try:
                inv = np.linalg.inv(st["A"])
                theta = inv @ st["b"]
                exploit = float(theta @ x_bar)
                explore = float(np.sqrt(max(x_bar @ inv @ x_bar, 0.0)))
                scores[arm] = exploit + ALPHA * explore if st["n"] else 0.0
            except np.linalg.LinAlgError:
                scores[arm] = 0.0
        if any(v != 0.0 for v in scores.values()):
            shifted = {a: s - min(scores.values()) for a, s in scores.items()}
            total = sum(shifted.values()) or 1.0
            weights = {a: round(s / total, 4) for a, s in shifted.items()}
        else:  # priors-only: uniform
            weights = {a: round(1.0 / len(ARMS), 4) for a in ARMS}
        clusters_out[cluster] = {
            "weights": weights, "counts": counts, "mean_reward": mean_rewards,
            "n_rows": ctx_n[cluster],
        }

    return {
        "model": "v1-linucb-per-cluster",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": n_used,
        "arms": ARMS,
        "clusters": clusters_out,
        "epsilon_greedy": EPSILON_CFG,
        "reward_rubric": {"accept": 1.0, "edited": 0.5, "rejected": 0.0},
        "notes": ("Priors-only uniform weights when n_rows==0. "
                  "Serving: epsilon-greedy over these weights; abstain floor "
                  "(confidence<0.60) from v0 is preserved and never overridden."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Train LinUCB-per-cluster bandit weights (offline).")
    ap.add_argument("--input", default=None, help="JSON file with rx_feedback rows.")
    ap.add_argument("--output", default=None,
                    help="Weights JSON path (default ds/models/bandit_weights.json).")
    ap.add_argument("--demo", action="store_true", help="Use 12 built-in sample rows.")
    args = ap.parse_args()

    rows = demo_rows() if args.demo else load_rows(args.input)
    if args.input and not args.demo:  # explicit path must exist; fail loud, don't silently train empty
        p = Path(args.input)
        if not p.exists():
            print(f"Input file not found: {p}", file=sys.stderr)
            return 2
    result = train(rows)

    out = Path(args.output) if args.output else Path(__file__).parent / "models" / "bandit_weights.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Trained on {result['n_rows']} rows -> {out}")
    for cluster, info in result["clusters"].items():
        if info["n_rows"]:
            top = max(info["weights"], key=info["weights"].get)
            print(f"  {cluster}: n={info['n_rows']} top={top} ({info['weights'][top]})")
        else:
            print(f"  {cluster}: n=0 (uniform priors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
