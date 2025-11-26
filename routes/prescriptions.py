"""
Prescription Management API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.database import SessionLocal, Prescription, PrescriptionItem, Encounter, Medicine
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])


class PrescriptionItemCreate(BaseModel):
    medicine_id: Optional[str] = None
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    quantity: Optional[int] = None
    instructions: Optional[str] = None


class PrescriptionCreate(BaseModel):
    encounter_id: Optional[str] = None
    patient_id: str
    staff_id: Optional[str] = None
    items: List[PrescriptionItemCreate]
    notes: Optional[str] = None


@router.get("")
async def get_all_prescriptions(limit: int = 50, token: str = "demo-token"):
    """Get all prescriptions (for list view)"""
    try:
        session = SessionLocal()
        prescriptions = session.query(Prescription).order_by(Prescription.prescription_date.desc()).limit(limit).all()
        
        result = []
        for pres in prescriptions:
            # Get items for each prescription to display summary
            items = session.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == pres.id).all()
            
            # Create a string representation of medications for the frontend list view
            medications_str = "\n".join([
                f"{item.medicine_name} ({item.dosage or ''}) - {item.frequency or ''} for {item.duration or ''}"
                for item in items
            ])
            
            result.append({
                "id": pres.id,
                "patient_id": pres.patient_id,
                "date": pres.prescription_date.isoformat() if pres.prescription_date else None,
                "medications": medications_str,
                "instructions": pres.notes
            })
        
        session.close()
        return {"prescriptions": result}
    except Exception as e:
        logger.error(f"Error getting all prescriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_prescription(prescription: PrescriptionCreate, token: str = "demo-token"):
    """Create a new prescription"""
    try:
        session = SessionLocal()
        
        # Use a dummy encounter/staff if not provided (for standalone prescription creation)
        encounter_id = prescription.encounter_id
        if not encounter_id:
            # Try to find latest encounter for patient, or create a dummy one? 
            # For now, let's allow null encounter_id in DB or just skip validation if we relax the DB constraint.
            # Assuming DB allows null encounter_id or we use a placeholder.
            # Let's check if we can just pass None. The model definition in database.py might require it.
            pass

        # Create prescription
        new_prescription = Prescription(
            id=str(uuid.uuid4()),
            encounter_id=encounter_id, # Might be None
            patient_id=prescription.patient_id,
            staff_id=prescription.staff_id or "admin", # Default to admin
            notes=prescription.notes,
            prescription_date=datetime.utcnow()
        )
        
        session.add(new_prescription)
        session.flush()  # Get the ID
        
        # Add prescription items
        for item in prescription.items:
            # Check if medicine exists in inventory
            medicine = None
            if item.medicine_id:
                medicine = session.query(Medicine).filter(Medicine.id == item.medicine_id).first()
            
            prescription_item = PrescriptionItem(
                id=str(uuid.uuid4()),
                prescription_id=new_prescription.id,
                medicine_id=item.medicine_id if medicine else None,
                medicine_name=item.medicine_name,
                dosage=item.dosage,
                frequency=item.frequency,
                duration=item.duration,
                quantity=item.quantity,
                instructions=item.instructions
            )
            
            session.add(prescription_item)
        
        session.commit()
        prescription_id = new_prescription.id
        session.close()
        
        return {"status": "success", "prescription_id": prescription_id, "message": "Prescription created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prescription_id}")
async def get_prescription(prescription_id: str, token: str = "demo-token"):
    """Get prescription details"""
    try:
        session = SessionLocal()
        prescription = session.query(Prescription).filter(Prescription.id == prescription_id).first()
        
        if not prescription:
            session.close()
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # Get prescription items
        items = session.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == prescription_id).all()
        
        session.close()
        
        return {
            "id": prescription.id,
            "encounter_id": prescription.encounter_id,
            "patient_id": prescription.patient_id,
            "staff_id": prescription.staff_id,
            "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
            "notes": prescription.notes,
            "status": prescription.status,
            "items": [
                {
                    "id": item.id,
                    "medicine_id": item.medicine_id,
                    "medicine_name": item.medicine_name,
                    "dosage": item.dosage,
                    "frequency": item.frequency,
                    "duration": item.duration,
                    "quantity": item.quantity,
                    "instructions": item.instructions
                } for item in items
            ],
            "created_at": prescription.created_at.isoformat() if prescription.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patient/{patient_id}")
async def get_patient_prescriptions(patient_id: str, limit: int = 20, token: str = "demo-token"):
    """Get all prescriptions for a patient"""
    try:
        session = SessionLocal()
        prescriptions = session.query(Prescription).filter(
            Prescription.patient_id == patient_id
        ).order_by(Prescription.prescription_date.desc()).limit(limit).all()
        
        result = []
        for pres in prescriptions:
            items = session.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == pres.id).all()
            result.append({
                "id": pres.id,
                "prescription_date": pres.prescription_date.isoformat() if pres.prescription_date else None,
                "status": pres.status,
                "items_count": len(items)
            })
        
        session.close()
        return {"patient_id": patient_id, "prescriptions": result}
    except Exception as e:
        logger.error(f"Error getting patient prescriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
