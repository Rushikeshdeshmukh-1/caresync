-- Migration 004: Fix bills_v2 table schema
-- Add missing columns to bills_v2 table

ALTER TABLE bills_v2 ADD COLUMN prescription_id TEXT;
ALTER TABLE bills_v2 ADD COLUMN paid_amount REAL DEFAULT 0;
ALTER TABLE bills_v2 ADD COLUMN payment_status TEXT DEFAULT 'unpaid' CHECK(payment_status IN ('paid', 'unpaid', 'partial'));
ALTER TABLE bills_v2 ADD COLUMN payment_method TEXT;
ALTER TABLE bills_v2 ADD COLUMN payment_date TIMESTAMP;
ALTER TABLE bills_v2 ADD COLUMN notes TEXT;

-- Add foreign key index
CREATE INDEX IF NOT EXISTS idx_bills_v2_prescription ON bills_v2(prescription_id);

-- Update bill_items_v2 to use 'amount' instead of 'line_total'
ALTER TABLE bill_items_v2 ADD COLUMN amount REAL;

-- Copy data from line_total to amount if exists
UPDATE bill_items_v2 SET amount = line_total WHERE amount IS NULL;
