# Bandit replay eval — v1 LinUCB vs v0 rules

Offline replay protocol for deciding whether the adaptive loop (`v1-linucb-per-cluster`,
weights in `ds/models/bandit_weights.json`) beats the frozen `v0-rules` baseline
(`ds/recommender.py`). No live Supabase writes; eval reads `rx_feedback` rows
(file export) and `orders.package_items` snapshots only.

## 1. Data sources

| Source | Rows | Fields used |
|---|---|---|
| `rx_feedback` export (JSON) | one row per doctor review | `suggested`, `approved`, `reward`, `ticket_id`, `created_at` |
| `orders` (read-only) | one row per dispensed order | `ticket_id`, `package_items` ([{name, quantity}]) |
| v0 replay | recomputed, never stored | `recommend(ticket, in_stock)` on the same tickets |

Join key is `ticket_id`: `rx_feedback.ticket_id = orders.ticket_id`. The
`approved` snapshot should equal what was finally ordered; where they differ,
`orders.package_items` is ground truth for "what the patient actually got" and
`approved` is ground truth for "what the doctor chose". Report the mismatch
rate alongside the metrics.

```sql
-- Per-ticket join used by the replay (read-only):
SELECT f.ticket_id, f.suggested, f.approved, f.reward, o.package_items
FROM rx_feedback f
LEFT JOIN orders o ON o.ticket_id = f.ticket_id
ORDER BY f.created_at;
```

## 2. Metrics (all computed from the join above)

### Acceptance rate (primary)

```
acceptance_rate = #(reward = 1.0) / #(all rows)
edit_rate       = #(reward = 0.5) / #(all rows)
rejection_rate  = #(reward = 0.0) / #(all rows)
```

`reward` is authoritative when present. If missing, derive per rubric:
approved set == suggested set → 1.0; approved empty → 0.0; else 0.5.
Report the share of derived (vs stored) rewards — a high derived share means
the rubric was applied post-hoc, not by the reviewing doctor.

### Edit distance (secondary, per row then averaged)

Medicine-set distance (order-insensitive, dose-insensitive):

```
edit_distance = 1 - |suggested ∩ approved| / |suggested ∪ approved|
                (0.0 when both empty; 1.0 when disjoint)
```

Report mean edit distance over non-accepted rows only (accepted rows are 0 by
definition and would dilute the signal), plus a dose-text change rate:
fraction of kept medicines whose dose string differs between `suggested` and
`approved`/`package_items`.

### Abstain rate (safety guardrail)

```
abstain_rate = #(v0 abstain = true) / #(all tickets recommended)
```

Recompute v0 abstain on each ticket via `recommend(ticket, in_stock)` and
compare against the bandit-gated policy (bandit NEVER clears a v0 abstain —
the `confidence < 0.60` floor is preserved; it may only abstain *more*).
Report both rates and the flip table (v0-abstain→bandit-propose must be zero).

## 3. Replay procedure

1. Export `rx_feedback` (+ joined `package_items`) to JSON — no DB writes.
2. Split rows by time: first 70% (by `created_at`) = train, last 30% = holdout.
3. Run `py -3.11 ds/train_bandit.py --input train.json --output /tmp/w.json`.
4. On holdout rows, simulate both arms with epsilon = 0 (pure exploit):
   v0 = recorded `suggested`; v1 = epsilon-greedy pick from `/tmp/w.json`
   weights for the row's symptom cluster. Score each against `approved`
   with the rubric + edit distance.
5. Report acceptance-rate delta (v1 − v0), mean edit distance delta, and
   both abstain rates, with n for each cell. Minimum n = 30 holdout rows
   before any ship decision; below that, report numbers as directional only.

## 4. What "beats v0" means (ship bar — ALL must hold)

- **Acceptance delta:** v1 holdout acceptance rate ≥ v0 + **5pp absolute**
  (paired rows, same tickets; no cherry-picked windows).
- **Abstain sane:** v1 abstain rate within ±2pp of v0, AND zero
  v0-abstain→v1-propose flips (safety floor intact).
- **Edits down or flat:** mean holdout edit distance does not increase
  by more than 0.05 vs v0.
- Else: keep serving v0, keep logging feedback, re-run replay next window.

## 5. Honest limitations

1. **Cold start:** with few or zero rows the trainer emits uniform priors
   (`n_rows == 0` → all weights 0.2), so v1 == random-tiebreak v0 and cannot
   demonstrate lift. The 5pp bar is unreachable until the train split covers
   every served cluster with ≥ ~10 rows each; until then the verdict is
   always "keep logging".
2. **Single-doctor bias:** early feedback comes from one (or few) reviewing
   doctors, so weights encode personal prescribing style (e.g. always dropping
   ORS), not consensus best practice. A positive replay delta may not survive
   a second reviewer — stratify acceptance by reviewer before shipping, and do
   not present bandit weights as clinical validation.

## 6. Safety note

Decision support only: the doctor always overrides, approvals persist via
`orders.package_items`, and the bandit only re-ranks in-stock formulary arms —
it can never invent a medicine, change a dose on its own, or clear a v0
abstain. Any eval that shows abstain-rate collapse or off-formulary proposals
is an automatic DISCARD regardless of acceptance delta.
