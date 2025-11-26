-- Rollback Migration: Drop V2 Tables
-- This script removes all v2 tables and returns to the original schema
-- WARNING: This will delete all data in v2 tables

-- Drop in reverse order to respect foreign key constraints

DROP INDEX IF EXISTS idx_audit_timestamp;
DROP INDEX IF EXISTS idx_audit_module;
DROP TABLE IF EXISTS module_audit_log;

DROP INDEX IF EXISTS idx_payments_v2_bill;
DROP INDEX IF EXISTS idx_bill_items_v2_bill;
DROP INDEX IF EXISTS idx_bills_v2_status;
DROP INDEX IF EXISTS idx_bills_v2_patient;
DROP TABLE IF EXISTS payments_v2;
DROP TABLE IF EXISTS bill_items_v2;
DROP TABLE IF EXISTS bills_v2;

DROP INDEX IF EXISTS idx_prescription_items_v2_prescription;
DROP INDEX IF EXISTS idx_prescriptions_v2_appointment;
DROP INDEX IF EXISTS idx_prescriptions_v2_doctor;
DROP INDEX IF EXISTS idx_prescriptions_v2_patient;
DROP TABLE IF EXISTS prescription_items_v2;
DROP TABLE IF EXISTS prescriptions_v2;

DROP INDEX IF EXISTS idx_appointments_v2_status;
DROP INDEX IF EXISTS idx_appointments_v2_start_time;
DROP INDEX IF EXISTS idx_appointments_v2_doctor;
DROP INDEX IF EXISTS idx_appointments_v2_patient;
DROP TABLE IF EXISTS appointments_v2;
