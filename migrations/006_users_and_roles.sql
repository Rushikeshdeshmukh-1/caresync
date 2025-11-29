-- Phase 1: Users and Roles Migration
-- Adds authentication and multi-role support to existing system

-- Extend users table with authentication fields
ALTER TABLE users ADD COLUMN password_hash TEXT;
ALTER TABLE users ADD COLUMN phone TEXT;
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;

-- Link patients to user accounts
ALTER TABLE patients ADD COLUMN user_id TEXT REFERENCES users(id);

-- Create clinicians table (extends staff model)
CREATE TABLE IF NOT EXISTS clinicians (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    staff_id TEXT REFERENCES staff(id),
    license_number TEXT,
    specialization TEXT,
    qualification TEXT,
    years_of_experience INTEGER,
    consultation_fee REAL,
    is_verified BOOLEAN DEFAULT FALSE,
    bio TEXT,
    languages_spoken TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create organizations table (clinics, hospitals, insurers)
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    org_type TEXT,  -- clinic, hospital, insurer, pharmacy
    address JSON,
    contact JSON,
    tax_id TEXT,
    license_number TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create org_users junction table
CREATE TABLE IF NOT EXISTS org_users (
    id TEXT PRIMARY KEY,
    org_id TEXT REFERENCES organizations(id),
    user_id TEXT REFERENCES users(id),
    role TEXT,  -- admin, member, viewer
    permissions JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, user_id)
);

-- Create refresh_tokens table for JWT refresh tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE
);

-- Create audit_logs table for all user actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT REFERENCES users(id),
    actor_type TEXT,  -- user, system, api
    action TEXT NOT NULL,
    resource TEXT,
    resource_id TEXT,
    payload JSON,
    ip_address TEXT,
    user_agent TEXT,
    status TEXT,  -- success, failed
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Seed default doctor account
INSERT OR IGNORE INTO users (id, name, email, role, created_at) 
VALUES ('doctor_main_001', 'Dr. Default', 'doctor@caresync.local', 'doctor', CURRENT_TIMESTAMP);

-- Create corresponding staff entry if not exists
INSERT OR IGNORE INTO staff (id, user_id, staff_type, specialization)
VALUES ('staff_001', 'doctor_main_001', 'doctor', 'General Practice');

-- Create clinician entry for default doctor
INSERT OR IGNORE INTO clinicians (id, user_id, staff_id, license_number, specialization, is_verified)
VALUES ('clinician_001', 'doctor_main_001', 'staff_001', 'MED-001', 'General Practice', TRUE);
