"""
Patient Management API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.database import SessionLocal, Patient, Clinic
from services.audit_service import AuditService
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/patients", tags=["patients"])
audit_service = AuditService()


class PatientCreate(BaseModel):
    name: str
    abha_id: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    family_history: Optional[str] = None
    clinic_id: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    family_history: Optional[str] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
async def create_patient(patient: PatientCreate, token: str = "demo-token"):
    """Register a new patient"""
    try:
        session = SessionLocal()
        
        # Check if ABHA ID already exists
        if patient.abha_id:
            existing = session.query(Patient).filter(Patient.abha_id == patient.abha_id).first()
            if existing:
                session.close()
                raise HTTPException(status_code=400, detail="Patient with this ABHA ID already exists")
        
        # Parse date of birth if provided
        dob = None
        if patient.date_of_birth:
            try:
                dob = datetime.fromisoformat(patient.date_of_birth.replace('Z', '+00:00'))
            except:
                pass
        
        new_patient = Patient(
            id=str(uuid.uuid4()),
            abha_id=patient.abha_id,
            name=patient.name,
            gender=patient.gender,
            date_of_birth=dob,
            age=patient.age,
            phone=patient.phone,
            email=patient.email,
            address=patient.address,
            emergency_contact=patient.emergency_contact,
            blood_group=patient.blood_group,
            allergies=patient.allergies,
            medical_history=patient.medical_history,
            family_history=patient.family_history,
            clinic_id=patient.clinic_id
        )
        
        session.add(new_patient)
        session.commit()
        patient_id = new_patient.id
        session.close()
        
        await audit_service.log_access(
            user_token=token,
            resource="patient",
            action="create",
            resource_id=patient_id
        )
        
        return {"status": "success", "patient_id": patient_id, "message": "Patient registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_patients(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    clinic_id: Optional[str] = None,
    token: str = "demo-token"
):
    """List patients with optional search and filtering"""
    try:
        session = SessionLocal()
        query = session.query(Patient)
        
        if search:
            query = query.filter(
                (Patient.name.ilike(f"%{search}%")) |
                (Patient.phone.ilike(f"%{search}%")) |
                (Patient.email.ilike(f"%{search}%")) |
                (Patient.abha_id.ilike(f"%{search}%"))
            )
        
        if clinic_id:
            query = query.filter(Patient.clinic_id == clinic_id)
        
        patients = query.offset(skip).limit(limit).all()
        total = query.count()
        session.close()
        
        result = []
        for p in patients:
            result.append({
                "id": p.id,
                "abha_id": p.abha_id,
                "name": p.name,
                "gender": p.gender,
                "age": p.age,
                "phone": p.phone,
                "email": p.email,
                "blood_group": p.blood_group,
                "clinic_id": p.clinic_id,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "patients": result
        }
    except Exception as e:
        logger.error(f"Error listing patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}")
async def get_patient(patient_id: str, token: str = "demo-token"):
    """Get patient details"""
    try:
        session = SessionLocal()
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        session.close()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "id": patient.id,
            "abha_id": patient.abha_id,
            "name": patient.name,
            "gender": patient.gender,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "age": patient.age,
            "phone": patient.phone,
            "email": patient.email,
            "address": patient.address,
            "emergency_contact": patient.emergency_contact,
            "blood_group": patient.blood_group,
            "allergies": patient.allergies,
            "medical_history": patient.medical_history,
            "family_history": patient.family_history,
            "clinic_id": patient.clinic_id,
            "created_at": patient.created_at.isoformat() if patient.created_at else None,
            "updated_at": patient.updated_at.isoformat() if patient.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{patient_id}")
async def update_patient(patient_id: str, patient: PatientUpdate, token: str = "demo-token"):
    """Update patient information"""
    try:
        session = SessionLocal()
        db_patient = session.query(Patient).filter(Patient.id == patient_id).first()
        
        if not db_patient:
            session.close()
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Update fields
        if patient.name is not None:
            db_patient.name = patient.name
        if patient.gender is not None:
            db_patient.gender = patient.gender
        if patient.date_of_birth is not None:
            try:
                db_patient.date_of_birth = datetime.fromisoformat(patient.date_of_birth.replace('Z', '+00:00'))
            except:
                pass
        if patient.age is not None:
            db_patient.age = patient.age
        if patient.phone is not None:
            db_patient.phone = patient.phone
        if patient.email is not None:
            db_patient.email = patient.email
        if patient.address is not None:
            db_patient.address = patient.address
        if patient.emergency_contact is not None:
            db_patient.emergency_contact = patient.emergency_contact
        if patient.blood_group is not None:
            db_patient.blood_group = patient.blood_group
        if patient.allergies is not None:
            db_patient.allergies = patient.allergies
        if patient.medical_history is not None:
            db_patient.medical_history = patient.medical_history
        if patient.family_history is not None:
            db_patient.family_history = patient.family_history
        
        db_patient.updated_at = datetime.utcnow()
        session.commit()
        session.close()
        
        await audit_service.log_access(
            user_token=token,
            resource="patient",
            action="update",
            resource_id=patient_id
        )
        
        return {"status": "success", "message": "Patient updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating patient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}/history")
async def get_patient_history(patient_id: str, token: str = "demo-token"):
    """Get patient medical history including encounters and diagnoses"""
    try:
        session = SessionLocal()
        from models.database import Encounter, EncounterDiagnosis, VitalSign
        
        # Get encounters
        encounters = session.query(Encounter).filter(Encounter.patient_id == patient_id).order_by(Encounter.visit_date.desc()).all()
        
        history = []
        for enc in encounters:
            # Get diagnoses
            diagnoses = session.query(EncounterDiagnosis).filter(EncounterDiagnosis.encounter_id == enc.id).all()
            # Get vital signs
            vitals = session.query(VitalSign).filter(VitalSign.encounter_id == enc.id).order_by(VitalSign.recorded_at.desc()).first()
            
            history.append({
                "encounter_id": enc.id,
                "visit_date": enc.visit_date.isoformat() if enc.visit_date else None,
                "chief_complaint": enc.chief_complaint,
                "diagnoses": [
                    {
                        "icd_code": d.icd_code,
                        "diagnosis_type": d.diagnosis_type,
                        "notes": d.notes
                    } for d in diagnoses
                ],
                "vital_signs": {
                    "temperature": vitals.temperature if vitals else None,
                    "blood_pressure": f"{vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic}" if vitals and vitals.blood_pressure_systolic else None,
                    "pulse": vitals.pulse if vitals else None,
                    "weight": vitals.weight if vitals else None
                } if vitals else None
            })
        
        session.close()
        return {"patient_id": patient_id, "history": history}
    except Exception as e:
        logger.error(f"Error getting patient history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
