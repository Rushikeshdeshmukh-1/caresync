-- Phase 3: Mapping Feedback & Co-Pilot Enhancement
-- Adds mapping feedback, proposals, and versioning for governance

-- Extend mapping_feedback table with additional fields
ALTER TABLE mapping_feedback ADD COLUMN ayush_term TEXT;
ALTER TABLE mapping_feedback ADD COLUMN suggested_icd11 TEXT;
ALTER TABLE mapping_feedback ADD COLUMN clinician_icd11 TEXT;
ALTER TABLE mapping_feedback ADD COLUMN encounter_id TEXT REFERENCES encounters(id);
ALTER TABLE mapping_feedback ADD COLUMN feedback_type TEXT DEFAULT 'correction';
ALTER TABLE mapping_feedback ADD COLUMN confidence_score REAL;

-- Create mapping_proposals table for admin review
CREATE TABLE IF NOT EXISTS mapping_proposals (
    id TEXT PRIMARY KEY,
    ayush_term TEXT NOT NULL,
    current_icd11 TEXT,
    proposed_icd11 TEXT NOT NULL,
    evidence JSON,  -- feedback IDs, acceptance rates, etc.
    reason TEXT,
    status TEXT DEFAULT 'pending',  -- pending, approved, rejected
    proposed_by TEXT REFERENCES users(id),
    reviewed_by TEXT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    notes TEXT
);

-- Create mapping_versions table for tracking changes
CREATE TABLE IF NOT EXISTS mapping_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    changes JSON,  -- list of mapping updates applied
    applied_by TEXT REFERENCES users(id),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    rollback_available BOOLEAN DEFAULT TRUE
);

-- Extend encounter_diagnoses for dual coding
ALTER TABLE encounter_diagnoses ADD COLUMN accepted_from_ai BOOLEAN DEFAULT FALSE;
ALTER TABLE encounter_diagnoses ADD COLUMN ai_suggestion_id TEXT;
ALTER TABLE encounter_diagnoses ADD COLUMN clinician_modified BOOLEAN DEFAULT FALSE;

-- Create indices
CREATE INDEX IF NOT EXISTS idx_mapping_feedback_ayush_term ON mapping_feedback(ayush_term);
CREATE INDEX IF NOT EXISTS idx_mapping_feedback_encounter ON mapping_feedback(encounter_id);
CREATE INDEX IF NOT EXISTS idx_mapping_proposals_status ON mapping_proposals(status);
CREATE INDEX IF NOT EXISTS idx_mapping_proposals_ayush_term ON mapping_proposals(ayush_term);
CREATE INDEX IF NOT EXISTS idx_encounter_diagnoses_ai_suggestion ON encounter_diagnoses(ai_suggestion_id);
