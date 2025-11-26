"""
Prescriptions V2 API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from services.prescriptions_v2.service import PrescriptionsService
from services.prescriptions_v2.models import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/prescriptions", tags=["Prescriptions V2"])

# Initialize service
prescriptions_service = PrescriptionsService()

@router.post("", response_model=dict, status_code=201)
async def create_prescription(prescription: PrescriptionCreate):
    """Create a new prescription with items"""
    try:
        # Convert camelCase to snake_case for service
        items_data = [
            {
                'medicine_name': item.medicine_name,
                'form': item.form,
                'dose': item.dose,
                'frequency': item.frequency,
                'duration': item.duration,
                'instructions': item.instructions
            }
            for item in prescription.items
        ]
        
        result = prescriptions_service.create_prescription(
            patient_id=prescription.patientId,
            doctor_id=prescription.doctorId,
            appointment_id=prescription.appointmentId,
            diagnosis=prescription.diagnosis,
            notes=prescription.notes,
            items=items_data
        )
        
        return {
            "message": "Prescription created successfully",
            "prescription": result
        }
    except Exception as e:
        logger.error(f"Error creating prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{prescription_id}", response_model=dict)
async def get_prescription(prescription_id: str):
    """Get prescription by ID"""
    try:
        prescription = prescriptions_service.get_prescription(prescription_id)
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return prescription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=dict)
async def list_prescriptions(
    patient_id: Optional[str] = Query(None),
    doctor_id: Optional[str] = Query(None),
    appointment_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List prescriptions with filters"""
    try:
        from_dt = datetime.fromisoformat(from_date) if from_date else None
        to_dt = datetime.fromisoformat(to_date) if to_date else None
        
        prescriptions = prescriptions_service.list_prescriptions(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_id=appointment_id,
            from_date=from_dt,
            to_date=to_dt,
            limit=limit,
            offset=offset
        )
        
        return {
            "prescriptions": prescriptions,
            "count": len(prescriptions),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing prescriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{prescription_id}", response_model=dict)
async def update_prescription(prescription_id: str, update: PrescriptionUpdate):
    """Update prescription"""
    try:
        prescription = prescriptions_service.update_prescription(
            prescription_id=prescription_id,
            diagnosis=update.diagnosis,
            notes=update.notes
        )
        
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return {
            "message": "Prescription updated successfully",
            "prescription": prescription
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{prescription_id}", response_model=dict)
async def delete_prescription(prescription_id: str):
    """Delete a prescription"""
    try:
        success = prescriptions_service.delete_prescription(prescription_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return {"message": "Prescription deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
