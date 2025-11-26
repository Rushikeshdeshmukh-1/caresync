"""
Billing V2 API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from services.billing_v2.service import BillingService
from services.billing_v2.models import (
    BillCreate,
    PaymentUpdate,
    BillResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/billing", tags=["Billing V2"])

# Initialize service
billing_service = BillingService()

@router.post("", response_model=dict, status_code=201)
async def create_bill(bill: BillCreate):
    """Create a new bill with items"""
    try:
        # Convert camelCase to snake_case for service
        items_data = [
            {
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'amount': item.amount
            }
            for item in bill.items
        ]
        
        result = billing_service.create_bill(
            patient_id=bill.patientId,
            appointment_id=bill.appointmentId,
            prescription_id=bill.prescriptionId,
            items=items_data,
            notes=bill.notes
        )
        
        return {
            "message": "Bill created successfully",
            "bill": result
        }
    except Exception as e:
        logger.error(f"Error creating bill: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bill_id}", response_model=dict)
async def get_bill(bill_id: str):
    """Get bill by ID"""
    try:
        bill = billing_service.get_bill(bill_id)
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        return bill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bill: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=dict)
async def list_bills(
    patient_id: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List bills with filters"""
    try:
        from_dt = datetime.fromisoformat(from_date) if from_date else None
        to_dt = datetime.fromisoformat(to_date) if to_date else None
        
        bills = billing_service.list_bills(
            patient_id=patient_id,
            payment_status=payment_status,
            from_date=from_dt,
            to_date=to_dt,
            limit=limit,
            offset=offset
        )
        
        return {
            "bills": bills,
            "count": len(bills),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing bills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bill_id}/payment", response_model=dict)
async def update_payment(bill_id: str, payment: PaymentUpdate):
    """Update payment information"""
    try:
        bill = billing_service.update_payment(
            bill_id=bill_id,
            paid_amount=payment.paidAmount,
            payment_method=payment.paymentMethod,
            payment_status=payment.paymentStatus
        )
        
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        return {
            "message": "Payment updated successfully",
            "bill": bill
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{bill_id}", response_model=dict)
async def delete_bill(bill_id: str):
    """Delete a bill"""
    try:
        success = billing_service.delete_bill(bill_id)
        if not success:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        return {"message": "Bill deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bill: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
