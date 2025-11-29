-- Phase 2: Appointments, Teleconsult & Payments Migration
-- Extends appointments for teleconsult and adds payment processing

-- Extend appointments table for teleconsult
ALTER TABLE appointments ADD COLUMN teleconsult_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE appointments ADD COLUMN room_token TEXT;
ALTER TABLE appointments ADD COLUMN room_url TEXT;
ALTER TABLE appointments ADD COLUMN session_started_at TIMESTAMP;
ALTER TABLE appointments ADD COLUMN session_ended_at TIMESTAMP;
ALTER TABLE appointments ADD COLUMN duration_minutes INTEGER;

-- Create payment_intents table
CREATE TABLE IF NOT EXISTS payment_intents (
    id TEXT PRIMARY KEY,
    appointment_id TEXT REFERENCES appointments(id),
    patient_id TEXT REFERENCES patients(id),
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    provider TEXT,  -- razorpay, stripe, cash
    provider_payment_id TEXT,
    provider_order_id TEXT,
    status TEXT DEFAULT 'pending',  -- pending, processing, succeeded, failed, cancelled, refunded
    payment_method TEXT,  -- card, upi, netbanking, wallet
    metadata JSON,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);

-- Create payment_webhooks table for webhook event tracking
CREATE TABLE IF NOT EXISTS payment_webhooks (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payment_intent_id TEXT REFERENCES payment_intents(id),
    payload JSON NOT NULL,
    signature TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create teleconsult_sessions table for session tracking
CREATE TABLE IF NOT EXISTS teleconsult_sessions (
    id TEXT PRIMARY KEY,
    appointment_id TEXT REFERENCES appointments(id),
    room_name TEXT NOT NULL,
    room_token TEXT,
    host_user_id TEXT REFERENCES users(id),
    participant_user_ids JSON,  -- Array of user IDs
    status TEXT DEFAULT 'scheduled',  -- scheduled, active, ended, cancelled
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    recording_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_payment_intents_appointment ON payment_intents(appointment_id);
CREATE INDEX IF NOT EXISTS idx_payment_intents_patient ON payment_intents(patient_id);
CREATE INDEX IF NOT EXISTS idx_payment_intents_status ON payment_intents(status);
CREATE INDEX IF NOT EXISTS idx_payment_webhooks_payment_intent ON payment_webhooks(payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_teleconsult_sessions_appointment ON teleconsult_sessions(appointment_id);
