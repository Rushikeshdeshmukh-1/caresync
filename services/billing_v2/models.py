"""
Pydantic models for Billing V2 API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BillItemCreate(BaseModel):
    """Model for creating a bill item"""
    description: str = Field(..., description="Item description")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Unit price")
    amount: float = Field(..., ge=0, description="Total amount")

class BillCreate(BaseModel):
    """Model for creating a bill"""
    patientId: str = Field(..., description="Patient ID")
    appointmentId: Optional[str] = Field(None, description="Related appointment ID")
    prescriptionId: Optional[str] = Field(None, description="Related prescription ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    items: List[BillItemCreate] = Field(default_factory=list, description="Bill items")

class PaymentUpdate(BaseModel):
    """Model for updating payment"""
    paidAmount: float = Field(..., ge=0, description="Amount paid")
    paymentMethod: Optional[str] = Field(None, description="Payment method (cash, card, upi, etc.)")
    paymentStatus: Optional[str] = Field(None, description="Payment status (paid, partial, unpaid)")

class BillItemResponse(BaseModel):
    """Model for bill item response"""
    id: str
    bill_id: str
    description: str
    quantity: int
    unit_price: float
    amount: float
    created_at: str

class BillResponse(BaseModel):
    """Model for bill response"""
    id: str
    patient_id: str
    appointment_id: Optional[str]
    prescription_id: Optional[str]
    total_amount: float
    paid_amount: float
    payment_status: str
    payment_method: Optional[str]
    payment_date: Optional[str]
    notes: Optional[str]
    created_at: str
    patient_name: Optional[str] = None
    items: List[dict] = []
