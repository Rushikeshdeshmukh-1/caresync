-- Migration 001: Create V2 Tables for Appointments, Prescriptions, and Billing
-- This migration creates new tables with _v2 suffix to avoid breaking existing code
-- Run this before data migration

-- ==================== Appointments V2 ====================

CREATE TABLE IF NOT EXISTS appointments_v2 (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')),
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES staff(id)
);

CREATE INDEX IF NOT EXISTS idx_appointments_v2_patient ON appointments_v2(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_v2_doctor ON appointments_v2(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_v2_start_time ON appointments_v2(start_time);
CREATE INDEX IF NOT EXISTS idx_appointments_v2_status ON appointments_v2(status);

-- ==================== Prescriptions V2 ====================

CREATE TABLE IF NOT EXISTS prescriptions_v2 (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    appointment_id TEXT,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    diagnosis TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES staff(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments_v2(id)
);

CREATE TABLE IF NOT EXISTS prescription_items_v2 (
    id TEXT PRIMARY KEY,
    prescription_id TEXT NOT NULL,
    medicine_name TEXT NOT NULL,
    form TEXT,
    dose TEXT,
    frequency TEXT,
    duration TEXT,
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions_v2(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_prescriptions_v2_patient ON prescriptions_v2(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_v2_doctor ON prescriptions_v2(doctor_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_v2_appointment ON prescriptions_v2(appointment_id);
CREATE INDEX IF NOT EXISTS idx_prescription_items_v2_prescription ON prescription_items_v2(prescription_id);

-- ==================== Billing V2 ====================

CREATE TABLE IF NOT EXISTS bills_v2 (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    appointment_id TEXT,
    status TEXT DEFAULT 'unpaid' CHECK(status IN ('paid', 'unpaid', 'partial', 'cancelled')),
    total_amount REAL NOT NULL,
    tax_amount REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments_v2(id)
);

CREATE TABLE IF NOT EXISTS bill_items_v2 (
    id TEXT PRIMARY KEY,
    bill_id TEXT NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price REAL NOT NULL,
    tax_percent REAL DEFAULT 0,
    line_total REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills_v2(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments_v2 (
    id TEXT PRIMARY KEY,
    bill_id TEXT NOT NULL,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    txn_ref TEXT,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills_v2(id)
);

CREATE INDEX IF NOT EXISTS idx_bills_v2_patient ON bills_v2(patient_id);
CREATE INDEX IF NOT EXISTS idx_bills_v2_status ON bills_v2(status);
CREATE INDEX IF NOT EXISTS idx_bill_items_v2_bill ON bill_items_v2(bill_id);
CREATE INDEX IF NOT EXISTS idx_payments_v2_bill ON payments_v2(bill_id);

-- ==================== Audit Table (Optional) ====================

CREATE TABLE IF NOT EXISTS module_audit_log (
    id TEXT PRIMARY KEY,
    module TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_id TEXT,
    user_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_module ON module_audit_log(module);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON module_audit_log(timestamp);
