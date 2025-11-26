"""
Appointment Scheduling API Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.database import SessionLocal, Appointment, Patient, Staff, Clinic
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/appointments", tags=["appointments"])


class AppointmentCreate(BaseModel):
    patient_id: str
    staff_id: Optional[str] = None
    clinic_id: Optional[str] = None
    department_id: Optional[str] = None
    appointment_date: str  # ISO format
    appointment_time: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


@router.post("")
async def create_appointment(appointment: AppointmentCreate, token: str = "demo-token"):
    """Book a new appointment"""
    try:
        session = SessionLocal()
        
        # Parse appointment date
        try:
            appt_date = datetime.fromisoformat(appointment.appointment_date.replace('Z', '+00:00'))
        except:
            raise HTTPException(status_code=400, detail="Invalid appointment_date format")
        
        # Verify patient exists
        patient = session.query(Patient).filter(Patient.id == appointment.patient_id).first()
        if not patient:
            session.close()
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Use default staff if not provided
        staff_id = appointment.staff_id
        if not staff_id:
            # Try to find any staff or use a placeholder
            staff = session.query(Staff).first()
            if staff:
                staff_id = staff.id
            else:
                # Create a dummy staff if none exists (for demo purposes)
                staff = Staff(id=str(uuid.uuid4()), name="Dr. Rushikesh", staff_type="doctor")
                session.add(staff)
                session.commit()
                staff_id = staff.id
        
        new_appointment = Appointment(
            id=str(uuid.uuid4()),
            patient_id=appointment.patient_id,
            staff_id=staff_id,
            clinic_id=appointment.clinic_id,
            department_id=appointment.department_id,
            appointment_date=appt_date,
            appointment_time=appointment.appointment_time,
            reason=appointment.reason,
            notes=appointment.notes,
            status='scheduled'
        )
        
        session.add(new_appointment)
        session.commit()
        appointment_id = new_appointment.id
        session.close()
        
        return {"status": "success", "appointment_id": appointment_id, "message": "Appointment booked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_appointments(
    skip: int = 0,
    limit: int = 50,
    patient_id: Optional[str] = None,
    staff_id: Optional[str] = None,
    clinic_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    token: str = "demo-token"
):
    """List appointments with filtering"""
    try:
        session = SessionLocal()
        query = session.query(Appointment)
        
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        if staff_id:
            query = query.filter(Appointment.staff_id == staff_id)
        if clinic_id:
            query = query.filter(Appointment.clinic_id == clinic_id)
        if status:
            query = query.filter(Appointment.status == status)
        
        # Join with Patient table to get patient names
        results = query.order_by(Appointment.appointment_date.desc()).offset(skip).limit(limit).all()
        
        # Get patient names manually for now (or use join if configured)
        appointments_list = []
        for apt in results:
            patient = session.query(Patient).filter(Patient.id == apt.patient_id).first()
            patient_name = patient.name if patient else "Unknown"
            
            appointments_list.append({
                "id": apt.id,
                "patient_id": apt.patient_id,
                "patient_name": patient_name,
                "staff_id": apt.staff_id,
                "date": apt.appointment_date.isoformat() if apt.appointment_date else None,
                "status": apt.status,
                "reason": apt.reason,
                "created_at": apt.created_at.isoformat() if apt.created_at else None
            })
            
        total = query.count()
        session.close()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "appointments": appointments_list
        }
    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{appointment_id}")
async def get_appointment(appointment_id: str, token: str = "demo-token"):
    """Get appointment details"""
    try:
        session = SessionLocal()
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        session.close()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "staff_id": appointment.staff_id,
            "clinic_id": appointment.clinic_id,
            "department_id": appointment.department_id,
            "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            "appointment_time": appointment.appointment_time,
            "status": appointment.status,
            "reason": appointment.reason,
            "notes": appointment.notes,
            "created_at": appointment.created_at.isoformat() if appointment.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{appointment_id}")
async def update_appointment(appointment_id: str, appointment: AppointmentUpdate, token: str = "demo-token"):
    """Update appointment"""
    try:
        session = SessionLocal()
        db_appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not db_appointment:
            session.close()
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        if appointment.appointment_date:
            try:
                db_appointment.appointment_date = datetime.fromisoformat(appointment.appointment_date.replace('Z', '+00:00'))
            except:
                pass
        if appointment.appointment_time is not None:
            db_appointment.appointment_time = appointment.appointment_time
        if appointment.status:
            db_appointment.status = appointment.status
        if appointment.reason is not None:
            db_appointment.reason = appointment.reason
        if appointment.notes is not None:
            db_appointment.notes = appointment.notes
        
        db_appointment.updated_at = datetime.utcnow()
        session.commit()
        session.close()
        
        return {"status": "success", "message": "Appointment updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{appointment_id}")
async def cancel_appointment(appointment_id: str, token: str = "demo-token"):
    """Cancel an appointment"""
    try:
        session = SessionLocal()
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appointment:
            session.close()
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment.status = 'cancelled'
        appointment.updated_at = datetime.utcnow()
        session.commit()
        session.close()
        
        return {"status": "success", "message": "Appointment cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
