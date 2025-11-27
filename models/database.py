"""
Database models and initialization
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, Boolean, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

database_url = os.getenv("DATABASE_URL", "sqlite:///./terminology.db")
engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """User model for clinicians and admins"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, default='clinician')  # clinician, admin
    clinic_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Clinic(Base):
    """Clinic model"""
    __tablename__ = "clinics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    address = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AyushTerm(Base):
    """AYUSH term model"""
    __tablename__ = "ayush_terms"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    term = Column(String, nullable=False, unique=True)
    language = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)


class IcdCode(Base):
    """ICD-11 code model"""
    __tablename__ = "icd_codes"
    
    code = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)


class MappingCandidate(Base):
    """Mapping candidate model"""
    __tablename__ = "mapping_candidates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ayush_term_id = Column(String, ForeignKey('ayush_terms.id'))
    icd_code = Column(String, ForeignKey('icd_codes.code'))
    confidence = Column(Float, nullable=True)
    provenance = Column(JSON, nullable=True)
    status = Column(String, default='candidate')
    created_at = Column(DateTime, default=datetime.utcnow)


class ClinicalRecord(Base):
    """Clinical record model for dual-coded entries"""
    __tablename__ = "clinical_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False)  # Pseudonymized
    clinician_id = Column(String, ForeignKey('users.id'))
    ayush_term_id = Column(String, ForeignKey('ayush_terms.id'))
    icd_code = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    consent = Column(Boolean, default=False)
    confidence = Column(Float, nullable=True)
    provenance = Column(JSON, nullable=True)
    synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MappingFeedback(Base):
    """Mapping feedback model for learning"""
    __tablename__ = "mapping_feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String, ForeignKey('clinical_records.id'))
    clinician_id = Column(String, ForeignKey('users.id'))
    action = Column(String, nullable=False)  # accepted, edited, rejected
    new_icd_code = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClaimsLog(Base):
    """Claims log for orchestration"""
    __tablename__ = "claims_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String, ForeignKey('clinical_records.id'))
    claim_json = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # SENT, PENDING, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Clinic Management Models ====================

class Patient(Base):
    """Patient model for clinic management"""
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    abha_id = Column(String, unique=True, nullable=True)  # ABHA Health ID
    name = Column(String, nullable=False)
    gender = Column(String, nullable=True)  # M, F, Other
    date_of_birth = Column(DateTime, nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(JSON, nullable=True)
    emergency_contact = Column(JSON, nullable=True)
    blood_group = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Department(Base):
    """Department model for clinic organization"""
    __tablename__ = "departments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Staff(Base):
    """Staff model for doctors, nurses, admin"""
    __tablename__ = "staff"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=True)
    department_id = Column(String, ForeignKey('departments.id'), nullable=True)
    staff_type = Column(String, nullable=False)  # doctor, nurse, admin, pharmacist
    specialization = Column(String, nullable=True)
    qualification = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Appointment(Base):
    """Appointment scheduling model"""
    __tablename__ = "appointments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey('patients.id'), nullable=False)
    staff_id = Column(String, ForeignKey('staff.id'), nullable=False)
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=True)
    department_id = Column(String, ForeignKey('departments.id'), nullable=True)
    appointment_date = Column(DateTime, nullable=False)
    appointment_time = Column(String, nullable=True)
    status = Column(String, default='scheduled')  # scheduled, confirmed, in_progress, completed, cancelled
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Encounter(Base):
    """Encounter/Visit model for patient visits"""
    __tablename__ = "encounters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey('patients.id'), nullable=False)
    staff_id = Column(String, ForeignKey('staff.id'), nullable=True)
    appointment_id = Column(String, ForeignKey('appointments.id'), nullable=True)
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=True)
    encounter_type = Column(String, default='outpatient')  # outpatient, inpatient, emergency
    chief_complaint = Column(Text, nullable=True)
    history_of_present_illness = Column(Text, nullable=True)
    examination = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    status = Column(String, default='in_progress')  # in_progress, completed
    visit_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VitalSign(Base):
    """Vital signs model"""
    __tablename__ = "vital_signs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=False)
    temperature = Column(Float, nullable=True)  # Celsius
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    pulse = Column(Integer, nullable=True)  # BPM
    respiratory_rate = Column(Integer, nullable=True)  # per minute
    oxygen_saturation = Column(Float, nullable=True)  # SpO2 %
    weight = Column(Float, nullable=True)  # kg
    height = Column(Float, nullable=True)  # cm
    bmi = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class EncounterDiagnosis(Base):
    """Diagnosis linked to encounter with double coding"""
    __tablename__ = "encounter_diagnoses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=False)
    ayush_term_id = Column(String, ForeignKey('ayush_terms.id'), nullable=True)
    icd_code = Column(String, nullable=False)
    diagnosis_type = Column(String, default='primary')  # primary, secondary, differential
    notes = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    provenance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Medicine(Base):
    """Medicine/Inventory model"""
    __tablename__ = "medicines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    generic_name = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    form = Column(String, nullable=True)  # tablet, capsule, syrup, injection
    strength = Column(String, nullable=True)  # 500mg, 10ml
    unit = Column(String, nullable=True)  # mg, ml, etc.
    batch_number = Column(String, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    unit_price = Column(Float, nullable=True)
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prescription(Base):
    """Prescription model"""
    __tablename__ = "prescriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=True) # Changed to nullable
    patient_id = Column(String, ForeignKey('patients.id'), nullable=False)
    staff_id = Column(String, ForeignKey('staff.id'), nullable=False)
    prescription_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    status = Column(String, default='active')  # active, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)


class PrescriptionItem(Base):
    """Prescription line items"""
    __tablename__ = "prescription_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prescription_id = Column(String, ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = Column(String, ForeignKey('medicines.id'), nullable=True)
    medicine_name = Column(String, nullable=False)  # In case medicine not in inventory
    dosage = Column(String, nullable=True)  # 500mg
    frequency = Column(String, nullable=True)  # twice daily, after meals
    duration = Column(String, nullable=True)  # 7 days, 2 weeks
    quantity = Column(Integer, nullable=True)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    """Invoice/Billing model"""
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=True)
    patient_id = Column(String, ForeignKey('patients.id'), nullable=False)
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=True)
    invoice_number = Column(String, unique=True, nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    status = Column(String, default='pending')  # pending, paid, partial, cancelled
    payment_method = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InvoiceItem(Base):
    """Invoice line items"""
    __tablename__ = "invoice_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey('invoices.id'), nullable=False)
    item_type = Column(String, nullable=False)  # consultation, medicine, procedure, test
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Payment transaction model"""
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey('invoices.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)  # cash, card, online, insurance
    payment_date = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Orchestration Models ====================

class OrchestratorAudit(Base):
    """Audit log for all orchestrator actions"""
    __tablename__ = "orchestrator_audit"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)  # encounter_processed, mapping_suggested, claim_generated, write_blocked
    actor = Column(String, default='orchestrator_agent')
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=True)
    resource_target = Column(String, nullable=True)  # Resource that was accessed/blocked
    payload_summary = Column(JSON, nullable=True)
    model_version = Column(String, nullable=True)
    evidence = Column(JSON, nullable=True)
    attempted_write = Column(Boolean, default=False)
    status = Column(String, nullable=False)  # success, blocked, failed
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ReviewQueue(Base):
    """Queue for items requiring human review"""
    __tablename__ = "review_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=False)
    reason = Column(String, nullable=False)  # low_confidence, mapping_correction, model_drift, blocked_write
    priority = Column(String, default='normal')  # low, normal, high, critical
    payload = Column(JSON, nullable=True)  # Full context for review
    assigned_to = Column(String, ForeignKey('users.id'), nullable=True)
    status = Column(String, default='open')  # open, in_progress, resolved, dismissed
    resolution = Column(JSON, nullable=True)  # Clinician's decision
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class ClaimPacket(Base):
    """Insurance claim packets (preview and submitted)"""
    __tablename__ = "claim_packets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=False)
    patient_id = Column(String, ForeignKey('patients.id'), nullable=False)
    insurer = Column(String, nullable=False)  # Insurer name/code
    claim_json = Column(JSON, nullable=False)  # Full claim payload
    status = Column(String, default='preview')  # preview, submitted, accepted, rejected
    submitted_by = Column(String, ForeignKey('users.id'), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    response = Column(JSON, nullable=True)  # Insurer response
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelMetrics(Base):
    """Time-series model performance metrics"""
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String, nullable=False)  # mapping_engine, reranker, ner_extractor
    model_version = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)  # acceptance_rate, avg_confidence, drift_score
    metric_value = Column(Float, nullable=False)
    meta_data = Column(JSON, nullable=True)  # Additional context (renamed from metadata)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class AISuggestion(Base):
    """AI suggestions for an encounter (read-only mapping references)"""
    __tablename__ = "ai_suggestions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=False)
    ayush_terms = Column(JSON, nullable=True)  # [{term, span_start, span_end}]
    suggestions = Column(JSON, nullable=True)  # [{icd11, confidence, explanation}]
    warnings = Column(JSON, nullable=True)     # [{code, severity, message}]
    followups = Column(JSON, nullable=True)    # suggested follow-up actions
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EncounterSummary(Base):
    """Auto-generated encounter summaries"""
    __tablename__ = "encounter_summaries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String, ForeignKey('encounters.id'), nullable=False)
    summary = Column(Text, nullable=True)
    patient_instructions = Column(Text, nullable=True)
    clinician_notes = Column(Text, nullable=True)
    generated_by = Column(String, default='copilot_agent')
    created_at = Column(DateTime, default=datetime.utcnow)



def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
