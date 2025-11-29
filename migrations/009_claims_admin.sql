-- Phase 4: Claims Processing & Admin Console
-- Adds claim packet generation and admin governance features

-- Create claim_packets table (if not exists)
CREATE TABLE IF NOT EXISTS claim_packets (
    id TEXT PRIMARY KEY,
    encounter_id TEXT REFERENCES encounters(id),
    patient_id TEXT REFERENCES patients(id),
    clinician_id TEXT REFERENCES users(id),
    insurer_id TEXT,
    claim_type TEXT,  -- ayush, icd11, dual
    payload JSON NOT NULL,
    status TEXT DEFAULT 'draft',  -- draft, submitted, approved, rejected, paid
    submitted_at TIMESTAMP,
    approved_at TIMESTAMP,
    amount_claimed REAL,
    amount_approved REAL,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create insurer_templates table
CREATE TABLE IF NOT EXISTS insurer_templates (
    id TEXT PRIMARY KEY,
    insurer_name TEXT NOT NULL,
    template_type TEXT,  -- fhir, custom_json, xml
    template_schema JSON NOT NULL,
    field_mappings JSON,
    validation_rules JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create admin_actions table for governance audit
CREATE TABLE IF NOT EXISTS admin_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id TEXT REFERENCES users(id),
    action_type TEXT NOT NULL,  -- approve_proposal, reject_proposal, apply_migration, etc.
    resource_type TEXT,
    resource_id TEXT,
    details JSON,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create system_config table for feature flags
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    value_type TEXT DEFAULT 'string',  -- string, boolean, number, json
    description TEXT,
    updated_by TEXT REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default system configs
INSERT OR IGNORE INTO system_config (key, value, value_type, description) VALUES
('enable_teleconsult', 'true', 'boolean', 'Enable teleconsult features'),
('enable_payments', 'true', 'boolean', 'Enable payment processing'),
('enable_claims', 'true', 'boolean', 'Enable claims generation'),
('orchestrator_status', 'active', 'string', 'Orchestrator status: active, paused, manual'),
('max_blocked_writes', '3', 'number', 'Max blocked writes before auto-pause');

-- Create indices
CREATE INDEX IF NOT EXISTS idx_claim_packets_encounter ON claim_packets(encounter_id);
CREATE INDEX IF NOT EXISTS idx_claim_packets_patient ON claim_packets(patient_id);
CREATE INDEX IF NOT EXISTS idx_claim_packets_status ON claim_packets(status);
CREATE INDEX IF NOT EXISTS idx_admin_actions_user ON admin_actions(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type);
