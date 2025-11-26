"""
Pydantic models for Prescriptions V2 API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PrescriptionItemCreate(BaseModel):
    """Model for creating a prescription item"""
    medicine_name: str = Field(..., description="Medicine name")
    form: Optional[str] = Field(None, description="Form (tablet, syrup, etc.)")
    dose: Optional[str] = Field(None, description="Dosage")
    frequency: Optional[str] = Field(None, description="Frequency")
    duration: Optional[str] = Field(None, description="Duration")
    instructions: Optional[str] = Field(None, description="Special instructions")

class PrescriptionCreate(BaseModel):
    """Model for creating a prescription"""
    patientId: str = Field(..., description="Patient ID")
    doctorId: str = Field(..., description="Doctor/Staff ID")
    appointmentId: Optional[str] = Field(None, description="Related appointment ID")
    diagnosis: Optional[str] = Field(None, description="Diagnosis")
    notes: Optional[str] = Field(None, description="Additional notes")
    items: List[PrescriptionItemCreate] = Field(default_factory=list, description="Prescription items")

class PrescriptionUpdate(BaseModel):
    """Model for updating a prescription"""
    diagnosis: Optional[str] = None
    notes: Optional[str] = None

class PrescriptionItemResponse(BaseModel):
    """Model for prescription item response"""
    id: str
    prescription_id: str
    medicine_name: str
    form: Optional[str]
    dose: Optional[str]
    frequency: Optional[str]
    duration: Optional[str]
    instructions: Optional[str]
    created_at: str

class PrescriptionResponse(BaseModel):
    """Model for prescription response"""
    id: str
    patient_id: str
    doctor_id: str
    appointment_id: Optional[str]
    issued_at: str
    diagnosis: Optional[str]
    notes: Optional[str]
    created_at: str
    patient_name: Optional[str] = None
    doctor_user_id: Optional[str] = None
    items: List[dict] = []
