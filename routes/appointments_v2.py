"""
Appointments V2 API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging

from services.appointments_v2.service import AppointmentsService
from services.appointments_v2.models import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/appointments", tags=["appointments-v2"])

# Initialize service
appointments_service = AppointmentsService()


@router.post("", response_model=dict)
async def create_appointment(appointment: AppointmentCreate, token: str = "demo-token"):
    """Create a new appointment"""
    try:
        result = appointments_service.create_appointment(
            patient_id=appointment.patientId,
            doctor_id=appointment.doctorId,
            start_time=appointment.startTime,
            end_time=appointment.endTime,
            reason=appointment.reason,
            notes=appointment.notes
        )
        
        return {
            "status": "success",
            "appointment": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{appointment_id}", response_model=dict)
async def get_appointment(appointment_id: str, token: str = "demo-token"):
    """Get appointment by ID"""
    try:
        appointment = appointments_service.get_appointment(appointment_id)
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "status": "success",
            "appointment": appointment
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=dict)
async def list_appointments(
    patientId: Optional[str] = Query(None),
    doctorId: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    token: str = "demo-token"
):
    """List appointments with filters"""
    try:
        # Parse dates
        from_dt = datetime.fromisoformat(from_date) if from_date else None
        to_dt = datetime.fromisoformat(to_date) if to_date else None
        
        # Calculate offset
        offset = (page - 1) * limit
        
        appointments = appointments_service.list_appointments(
            patient_id=patientId,
            doctor_id=doctorId,
            status=status,
            from_date=from_dt,
            to_date=to_dt,
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "appointments": appointments,
            "page": page,
            "limit": limit,
            "total": len(appointments)
        }
    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar", response_model=dict)
async def get_calendar(
    doctorId: str = Query(...),
    from_date: str = Query(..., alias="from"),
    to_date: str = Query(..., alias="to"),
    token: str = "demo-token"
):
    """Get calendar view for a doctor"""
    try:
        from_dt = datetime.fromisoformat(from_date)
        to_dt = datetime.fromisoformat(to_date)
        
        appointments = appointments_service.get_calendar(
            doctor_id=doctorId,
            from_date=from_dt,
            to_date=to_dt
        )
        
        return {
            "status": "success",
            "appointments": appointments
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{appointment_id}", response_model=dict)
async def update_appointment(
    appointment_id: str,
    appointment: AppointmentUpdate,
    token: str = "demo-token"
):
    """Update an appointment"""
    try:
        updates = appointment.dict(exclude_unset=True)
        
        # Convert datetime objects to match service expectations
        if 'startTime' in updates:
            updates['start_time'] = updates.pop('startTime')
        if 'endTime' in updates:
            updates['end_time'] = updates.pop('endTime')
        
        result = appointments_service.update_appointment(appointment_id, **updates)
        
        if not result:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "status": "success",
            "appointment": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{appointment_id}", response_model=dict)
async def delete_appointment(appointment_id: str, token: str = "demo-token"):
    """Delete an appointment"""
    try:
        success = appointments_service.delete_appointment(appointment_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "status": "success",
            "message": "Appointment deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{appointment_id}/cancel", response_model=dict)
async def cancel_appointment(appointment_id: str, token: str = "demo-token"):
    """Cancel an appointment"""
    try:
        result = appointments_service.cancel_appointment(appointment_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "status": "success",
            "appointment": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
