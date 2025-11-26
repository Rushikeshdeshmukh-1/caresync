"""
Encounter/Visit Management API Routes with NAMASTE-ICD-11 Integration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.database import SessionLocal, Encounter, EncounterDiagnosis, VitalSign, Patient, Staff
from services.mapping_engine import MappingEngine
from services.faiss_index import FaissIndex
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/encounters", tags=["encounters"])

# Mapping engine will be initialized in main.py startup
mapping_engine = None


class EncounterCreate(BaseModel):
    patient_id: str
    staff_id: str
    appointment_id: Optional[str] = None
    clinic_id: Optional[str] = None
    encounter_type: Optional[str] = "outpatient"
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    examination: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None


class VitalSignCreate(BaseModel):
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    pulse: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None


class DiagnosisAdd(BaseModel):
    ayush_term: Optional[str] = None  # NAMASTE term
    icd_code: str  # ICD-11 code
    diagnosis_type: Optional[str] = "primary"
    notes: Optional[str] = None


@router.get("")
async def list_encounters(
    skip: int = 0,
    limit: int = 50,
    patient_id: Optional[str] = None,
    staff_id: Optional[str] = None,
    clinic_id: Optional[str] = None,
    status: Optional[str] = None,
    token: str = "demo-token"
):
    """List encounters with filtering"""
    try:
        session = SessionLocal()
        query = session.query(Encounter)
        
        if patient_id:
            query = query.filter(Encounter.patient_id == patient_id)
        if staff_id:
            query = query.filter(Encounter.staff_id == staff_id)
        if clinic_id:
            query = query.filter(Encounter.clinic_id == clinic_id)
        if status:
            query = query.filter(Encounter.status == status)
        
        encounters = query.order_by(Encounter.visit_date.desc()).offset(skip).limit(limit).all()
        total = query.count()
        session.close()
        
        result = []
        for enc in encounters:
            result.append({
                "id": enc.id,
                "patient_id": enc.patient_id,
                "staff_id": enc.staff_id,
                "appointment_id": enc.appointment_id,
                "clinic_id": enc.clinic_id,
                "encounter_type": enc.encounter_type,
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
async def create_encounter(encounter: EncounterCreate, token: str = "demo-token"):
    """Create a new patient encounter/visit"""
    try:
        session = SessionLocal()
        
        # Verify patient exists
        patient = session.query(Patient).filter(Patient.id == encounter.patient_id).first()
        if not patient:
            session.close()
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify staff exists
        staff = session.query(Staff).filter(Staff.id == encounter.staff_id).first()
        if not staff:
            session.close()
            raise HTTPException(status_code=404, detail="Staff not found")
        
        new_encounter = Encounter(
            id=str(uuid.uuid4()),
            patient_id=encounter.patient_id,
            staff_id=encounter.staff_id,
            appointment_id=encounter.appointment_id,
            clinic_id=encounter.clinic_id,
            encounter_type=encounter.encounter_type,
            chief_complaint=encounter.chief_complaint,
            history_of_present_illness=encounter.history_of_present_illness,
            examination=encounter.examination,
            assessment=encounter.assessment,
            plan=encounter.plan,
            status='in_progress'
        )
        
        session.add(new_encounter)
        session.commit()
        encounter_id = new_encounter.id
        session.close()
        
        return {"status": "success", "encounter_id": encounter_id, "message": "Encounter created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating encounter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{encounter_id}")
async def get_encounter(encounter_id: str, token: str = "demo-token"):
    """Get encounter details with diagnoses and vital signs"""
    try:
        session = SessionLocal()
        encounter = session.query(Encounter).filter(Encounter.id == encounter_id).first()
        
        if not encounter:
            session.close()
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        # Get diagnoses
        diagnoses = session.query(EncounterDiagnosis).filter(EncounterDiagnosis.encounter_id == encounter_id).all()
        # Get vital signs
        vitals = session.query(VitalSign).filter(VitalSign.encounter_id == encounter_id).order_by(VitalSign.recorded_at.desc()).all()
        
        session.close()
        
        return {
            "id": encounter.id,
            "patient_id": encounter.patient_id,
            "staff_id": encounter.staff_id,
            "appointment_id": encounter.appointment_id,
            "clinic_id": encounter.clinic_id,
            "encounter_type": encounter.encounter_type,
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


@router.post("/{encounter_id}/suggest-diagnosis")
async def suggest_diagnosis(encounter_id: str, term: str, k: int = 3, token: str = "demo-token"):
    """Suggest ICD-11 codes for a NAMASTE term using mapping engine"""
    try:
        # Import mapping engine from main
        from main import mapping_engine as main_mapping_engine
        if main_mapping_engine is None:
            raise HTTPException(status_code=503, detail="Mapping engine not initialized")
        
        # Use mapping engine to get suggestions
        result = main_mapping_engine.suggest(term, k=k)
        
        return {
            "status": "ok",
            "encounter_id": encounter_id,
            "term": term,
            "suggestions": result.get('results', []),
            "type": result.get('type', 'unknown')
        }
    except Exception as e:
        logger.error(f"Error suggesting diagnosis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{encounter_id}/diagnosis")
async def add_diagnosis(encounter_id: str, diagnosis: DiagnosisAdd, token: str = "demo-token"):
    """Add diagnosis to encounter with double coding (NAMASTE + ICD-11)"""
    try:
        session = SessionLocal()
        
        # Verify encounter exists
        encounter = session.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            session.close()
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        # Get or create AYUSH term if provided
        from models.database import AyushTerm
        ayush_term_id = None
        if diagnosis.ayush_term:
            ayush_term = session.query(AyushTerm).filter(AyushTerm.term == diagnosis.ayush_term).first()
            if not ayush_term:
                ayush_term = AyushTerm(
                    id=str(uuid.uuid4()),
                    term=diagnosis.ayush_term,
                    source="user_input"
                )
                session.add(ayush_term)
                session.commit()
            ayush_term_id = ayush_term.id
        
        # Create diagnosis entry
        new_diagnosis = EncounterDiagnosis(
            id=str(uuid.uuid4()),
            encounter_id=encounter_id,
            ayush_term_id=ayush_term_id,
            icd_code=diagnosis.icd_code,
            diagnosis_type=diagnosis.diagnosis_type,
            notes=diagnosis.notes
        )
        
        session.add(new_diagnosis)
        session.commit()
        diagnosis_id = new_diagnosis.id
        session.close()
        
        return {"status": "success", "diagnosis_id": diagnosis_id, "message": "Diagnosis added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding diagnosis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{encounter_id}/vitals")
async def record_vitals(encounter_id: str, vitals: VitalSignCreate, token: str = "demo-token"):
    """Record vital signs for an encounter"""
    try:
        session = SessionLocal()
        
        # Verify encounter exists
        encounter = session.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            session.close()
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        # Calculate BMI if weight and height provided
        bmi = None
        if vitals.weight and vitals.height:
            height_m = vitals.height / 100  # Convert cm to meters
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
        
        session.add(new_vitals)
        session.commit()
        vitals_id = new_vitals.id
        session.close()
        
        return {"status": "success", "vitals_id": vitals_id, "message": "Vital signs recorded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording vitals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{encounter_id}")
async def update_encounter(encounter_id: str, encounter_data: EncounterCreate, token: str = "demo-token"):
    """Update encounter details"""
    try:
        session = SessionLocal()
        encounter = session.query(Encounter).filter(Encounter.id == encounter_id).first()
        
        if not encounter:
            session.close()
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        if encounter_data.chief_complaint is not None:
            encounter.chief_complaint = encounter_data.chief_complaint
        if encounter_data.history_of_present_illness is not None:
            encounter.history_of_present_illness = encounter_data.history_of_present_illness
        if encounter_data.examination is not None:
            encounter.examination = encounter_data.examination
        if encounter_data.assessment is not None:
            encounter.assessment = encounter_data.assessment
        if encounter_data.plan is not None:
            encounter.plan = encounter_data.plan
        
        encounter.updated_at = datetime.utcnow()
        session.commit()
        session.close()
        
        return {"status": "success", "message": "Encounter updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating encounter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{encounter_id}/complete")
async def complete_encounter(encounter_id: str, token: str = "demo-token"):
    """Mark encounter as completed"""
    try:
        session = SessionLocal()
        encounter = session.query(Encounter).filter(Encounter.id == encounter_id).first()
        
        if not encounter:
            session.close()
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        encounter.status = 'completed'
        encounter.updated_at = datetime.utcnow()
        session.commit()
        session.close()
        
        return {"status": "success", "message": "Encounter completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing encounter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
