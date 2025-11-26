"""
Pydantic models for Appointments V2 API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AppointmentCreate(BaseModel):
    """Model for creating an appointment"""
    patientId: str = Field(..., description="Patient ID")
    doctorId: str = Field(..., description="Doctor/Staff ID")
    startTime: datetime = Field(..., description="Appointment start time (ISO format)")
    endTime: datetime = Field(..., description="Appointment end time (ISO format)")
    reason: Optional[str] = Field(None, description="Reason for appointment")
    notes: Optional[str] = Field(None, description="Additional notes")

class AppointmentUpdate(BaseModel):
    """Model for updating an appointment"""
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None
    status: Optional[str] = Field(None, description="scheduled, confirmed, in_progress, completed, cancelled, no_show")
    reason: Optional[str] = None
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    """Model for appointment response"""
    id: str
    patient_id: str
    doctor_id: str
    start_time: str
    end_time: str
    status: str
    reason: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str
    patient_name: Optional[str] = None
    doctor_user_id: Optional[str] = None
