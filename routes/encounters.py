"""
Encounter/Visit Management API Routes
Simplified and Robust Implementation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging
from sqlalchemy.orm import Session

from models.database import SessionLocal, Encounter, EncounterDiagnosis, VitalSign, Patient, Staff, AyushTerm

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/encounters", tags=["encounters"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---

class EncounterCreate(BaseModel):
    patient_id: str
    # staff_id is optional as per frontend
    staff_id: Optional[str] = None
    chief_complaint: str
    # Optional fields
    appointment_id: Optional[str] = None
    clinic_id: Optional[str] = None
    encounter_type: Optional[str] = "outpatient"
    history_of_present_illness: Optional[str] = None
    examination: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None

class EncounterResponse(BaseModel):
    id: str
    patient_id: str
    staff_id: Optional[str]
    chief_complaint: Optional[str]
    status: str
    visit_date: Optional[datetime]
    created_at: Optional[datetime]
    
    # Include patient name for convenience if needed, but keeping it simple for now
    
    class Config:
        orm_mode = True

class DiagnosisAdd(BaseModel):
    ayush_term: Optional[str] = None
    icd_code: str
    diagnosis_type: Optional[str] = "primary"
    notes: Optional[str] = None

class VitalSignCreate(BaseModel):
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    pulse: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None

# --- Routes ---

@router.get("")
async def list_encounters(
    skip: int = 0,
    limit: int = 50,
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List encounters with filtering"""
    try:
        query = db.query(Encounter)
        
        if patient_id:
            query = query.filter(Encounter.patient_id == patient_id)
        if status:
            query = query.filter(Encounter.status == status)
        
        # Order by most recent first
        encounters = query.order_by(Encounter.visit_date.desc()).offset(skip).limit(limit).all()
        total = query.count()
        
        # Manual serialization to avoid Pydantic recursion issues if any
        result = []
        for enc in encounters:
            # Fetch patient name if possible, or just return IDs
            patient_name = "Unknown"
            if enc.patient_id:
                patient = db.query(Patient).filter(Patient.id == enc.patient_id).first()
                if patient:
                    patient_name = patient.name

            result.append({
                "id": enc.id,
                "patient_id": enc.patient_id,
                "patient_name": patient_name,
                "staff_id": enc.staff_id,
                "chief_complaint": enc.chief_complaint,
                "status": enc.status,
                "visit_date": enc.visit_date.isoformat() if enc.visit_date else None,
                "created_at": enc.created_at.isoformat() if enc.created_at else None
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "encounters": result
        }
    except Exception as e:
        logger.error(f"Error listing encounters: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_encounter(encounter: EncounterCreate, db: Session = Depends(get_db)):
    """Create a new encounter"""
    try:
        # 1. Verify patient exists
        patient = db.query(Patient).filter(Patient.id == encounter.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # 2. Handle staff_id
        staff_id = encounter.staff_id
        if not staff_id:
            # Try to find a default staff member if none provided
            # This is a fallback to ensure we have some staff associated if possible, 
            # but since we made the column nullable, we can also leave it None.
            # Let's try to assign to the first staff member found, or leave None.
            first_staff = db.query(Staff).first()
            if first_staff:
                staff_id = first_staff.id
        
        # 3. Create Encounter
        new_encounter = Encounter(
            id=str(uuid.uuid4()),
            patient_id=encounter.patient_id,
            staff_id=staff_id, # Can be None now
            appointment_id=encounter.appointment_id,
            clinic_id=encounter.clinic_id,
            encounter_type=encounter.encounter_type,
            chief_complaint=encounter.chief_complaint,
            history_of_present_illness=encounter.history_of_present_illness,
            examination=encounter.examination,
            assessment=encounter.assessment,
            plan=encounter.plan,
            status='in_progress',
            visit_date=datetime.utcnow()
        )
        
        db.add(new_encounter)
        db.commit()
        db.refresh(new_encounter)
        
        return {
            "status": "success", 
            "encounter_id": new_encounter.id, 
            "message": "Encounter created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating encounter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{encounter_id}")
async def get_encounter(encounter_id: str, db: Session = Depends(get_db)):
    """Get encounter details"""
    try:
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        # Get diagnoses
        diagnoses = db.query(EncounterDiagnosis).filter(EncounterDiagnosis.encounter_id == encounter_id).all()
        
        # Get vitals
        vitals = db.query(VitalSign).filter(VitalSign.encounter_id == encounter_id).order_by(VitalSign.recorded_at.desc()).all()
        
        # Get patient details
        patient = db.query(Patient).filter(Patient.id == encounter.patient_id).first()
        
        return {
            "id": encounter.id,
            "patient_id": encounter.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "staff_id": encounter.staff_id,
            "chief_complaint": encounter.chief_complaint,
            "history_of_present_illness": encounter.history_of_present_illness,
            "examination": encounter.examination,
            "assessment": encounter.assessment,
            "plan": encounter.plan,
            "status": encounter.status,
            "visit_date": encounter.visit_date.isoformat() if encounter.visit_date else None,
            "diagnoses": [
                {
                    "id": d.id,
                    "icd_code": d.icd_code,
                    "diagnosis_type": d.diagnosis_type,
                    "notes": d.notes,
                    "confidence": d.confidence
                } for d in diagnoses
            ],
            "vital_signs": [
                {
                    "temperature": v.temperature,
                    "blood_pressure": f"{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}" if v.blood_pressure_systolic else None,
                    "pulse": v.pulse,
                    "respiratory_rate": v.respiratory_rate,
                    "oxygen_saturation": v.oxygen_saturation,
                    "weight": v.weight,
                    "height": v.height,
                    "bmi": v.bmi,
                    "recorded_at": v.recorded_at.isoformat() if v.recorded_at else None
                } for v in vitals
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting encounter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{encounter_id}/diagnosis")
async def add_diagnosis(encounter_id: str, diagnosis: DiagnosisAdd, db: Session = Depends(get_db)):
    """Add diagnosis to encounter"""
    try:
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
            
        # Handle Ayush Term
        ayush_term_id = None
        if diagnosis.ayush_term:
            ayush_term = db.query(AyushTerm).filter(AyushTerm.term == diagnosis.ayush_term).first()
            if not ayush_term:
                ayush_term = AyushTerm(
                    id=str(uuid.uuid4()),
                    term=diagnosis.ayush_term,
                    source="user_input"
                )
                db.add(ayush_term)
                db.commit()
            ayush_term_id = ayush_term.id
            
        new_diagnosis = EncounterDiagnosis(
            id=str(uuid.uuid4()),
            encounter_id=encounter_id,
            ayush_term_id=ayush_term_id,
            icd_code=diagnosis.icd_code,
            diagnosis_type=diagnosis.diagnosis_type,
            notes=diagnosis.notes
        )
        
        db.add(new_diagnosis)
        db.commit()
        
        return {"status": "success", "diagnosis_id": new_diagnosis.id}
    except Exception as e:
        logger.error(f"Error adding diagnosis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{encounter_id}/vitals")
async def record_vitals(encounter_id: str, vitals: VitalSignCreate, db: Session = Depends(get_db)):
    """Record vitals"""
    try:
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
            
        # Calculate BMI
        bmi = None
        if vitals.weight and vitals.height:
            height_m = vitals.height / 100
            if height_m > 0:
                bmi = vitals.weight / (height_m ** 2)
                
        new_vitals = VitalSign(
            id=str(uuid.uuid4()),
            encounter_id=encounter_id,
            temperature=vitals.temperature,
            blood_pressure_systolic=vitals.blood_pressure_systolic,
            blood_pressure_diastolic=vitals.blood_pressure_diastolic,
            pulse=vitals.pulse,
            respiratory_rate=vitals.respiratory_rate,
            oxygen_saturation=vitals.oxygen_saturation,
            weight=vitals.weight,
            height=vitals.height,
            bmi=bmi
        )
        
        db.add(new_vitals)
        db.commit()
        
        return {"status": "success", "vitals_id": new_vitals.id}
    except Exception as e:
        logger.error(f"Error recording vitals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{encounter_id}/complete")
async def complete_encounter(encounter_id: str, db: Session = Depends(get_db)):
    """Mark encounter as completed"""
    try:
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
            
        encounter.status = 'completed'
        encounter.updated_at = datetime.utcnow()
        db.commit()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error completing encounter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Note: suggest-diagnosis endpoint removed for now to simplify. 
# Can be re-added if needed, but should be robust.
