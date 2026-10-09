-- setup_rx_feedback.sql
-- Adaptive-loop feedback store for the prescribing recommender (v1 bandit upgrade).
-- NEW file: complements setup_supabase.sql. Run once in Supabase SQL editor.
-- No changes to existing tables. Writers insert one row per doctor review;
-- ds/train_bandit.py replays these rows OFFLINE (file export) to fit
-- per-symptom-cluster LinUCB weights. Live Supabase writes are out of scope
-- for the offline trainer; export rows to JSON and pass via --input.
--
-- Reward rubric (stored in `reward`, see column comment below):
--   accept-as-is  -> 1.0
--   edited        -> 0.5   (partial overlap: kept some, dropped/changed some)
--   rejected      -> 0.0   (approved empty / nothing kept)

-- uuid_generate_v4() needs pgcrypto; guard here (setup_supabase.sql assumes it exists).
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS rx_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES tickets(id) ON DELETE SET NULL,
    suggested JSONB NOT NULL DEFAULT '[]'::jsonb,
    approved JSONB NOT NULL DEFAULT '[]'::jsonb,
    reward FLOAT NOT NULL DEFAULT 0.0 CHECK (reward >= 0.0 AND reward <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE rx_feedback IS
'One row per doctor review of a v0/v1 prescribing suggestion. Suggested vs approved medicine sets + reward rubric (accept 1.0 / edited 0.5 / rejected 0.0) feed the offline LinUCB replay in ds/train_bandit.py.';

COMMENT ON COLUMN rx_feedback.id IS
'Primary key: random UUID per feedback event (uuid_generate_v4()).';

COMMENT ON COLUMN rx_feedback.ticket_id IS
'FK to tickets(id), nullable; ON DELETE SET NULL so feedback survives ticket cleanup. NULL allowed for synthetic/demo rows.';

COMMENT ON COLUMN rx_feedback.suggested IS
'JSONB snapshot of what the recommender proposed: list of medicine names or [{medicine, dose, ...}] objects as returned in v0 `suggestions`. Compared against `approved` to derive reward.';

COMMENT ON COLUMN rx_feedback.approved IS
'JSONB snapshot of what the doctor actually ordered: list of medicine names or [{medicine/name, quantity, ...}] objects mirroring orders.package_items. Empty list means full rejection.';

COMMENT ON COLUMN rx_feedback.reward IS
'Float in [0,1] per rubric: 1.0 accept-as-is (approved set equals suggested set), 0.5 edited (partial overlap or dose change), 0.0 rejected (approved empty / nothing kept). Enforced by CHECK constraint.';

COMMENT ON COLUMN rx_feedback.created_at IS
'Timestamptz of the review event, defaults to NOW(). Used to order replay and to window recent-vs-all acceptance rates.';

-- Replay lookups: per-ticket history and recent-window scans for eval.
CREATE INDEX IF NOT EXISTS idx_rx_feedback_ticket_id ON rx_feedback (ticket_id);
CREATE INDEX IF NOT EXISTS idx_rx_feedback_created_at ON rx_feedback (created_at DESC);

-- Hackathon convention (matches setup_supabase.sql): no RLS complications.
ALTER TABLE rx_feedback DISABLE ROW LEVEL SECURITY;
