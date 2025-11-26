"""
Billing and Invoice Management API Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from models.database import SessionLocal, Invoice, InvoiceItem, Payment, Encounter, Patient
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/invoices", tags=["billing"])


class InvoiceItemCreate(BaseModel):
    item_type: Optional[str] = "service"  # consultation, medicine, procedure, test
    item_name: Optional[str] = None
    description: Optional[str] = None # Alias for item_name
    quantity: int = 1
    unit_price: Optional[float] = None
    amount: Optional[float] = None # Alias for unit_price


class InvoiceCreate(BaseModel):
    encounter_id: Optional[str] = None
    patient_id: str
    clinic_id: Optional[str] = None
    items: List[InvoiceItemCreate]
    amount: Optional[float] = None # Total amount if items are simple
    tax: Optional[float] = 0.0
    discount: Optional[float] = 0.0
    notes: Optional[str] = None
    status: Optional[str] = "pending"


class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str  # cash, card, online, insurance
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
async def list_invoices(limit: int = 50, token: str = "demo-token"):
    """List all invoices"""
    try:
        session = SessionLocal()
        invoices = session.query(Invoice).order_by(Invoice.invoice_date.desc()).limit(limit).all()
        
        result = []
        for inv in invoices:
            result.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "patient_id": inv.patient_id,
                "date": inv.invoice_date.isoformat() if inv.invoice_date else None,
                "amount": inv.total,
                "status": inv.status
            })
        
        session.close()
        return {"invoices": result}
    except Exception as e:
        logger.error(f"Error listing invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_invoice(invoice: InvoiceCreate, token: str = "demo-token"):
    """Create a new invoice"""
    try:
        session = SessionLocal()
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Process items and calculate totals
        processed_items = []
        subtotal = 0.0
        
        for item in invoice.items:
            # Handle aliases
            name = item.item_name or item.description or "Service"
            price = item.unit_price or item.amount or 0.0
            
            processed_items.append({
                "item_type": item.item_type,
                "item_name": name,
                "quantity": item.quantity,
                "unit_price": price,
                "total": price * item.quantity
            })
            subtotal += price * item.quantity
            
        # If total amount is provided directly and overrides calculation (simple mode)
        if invoice.amount and subtotal == 0:
            subtotal = invoice.amount
            # Add a generic item if none exist
            if not processed_items:
                processed_items.append({
                    "item_type": "service",
                    "item_name": "Consultation / Service",
                    "quantity": 1,
                    "unit_price": subtotal,
                    "total": subtotal
                })

        total = subtotal + invoice.tax - invoice.discount
        
        # Create invoice
        new_invoice = Invoice(
            id=str(uuid.uuid4()),
            encounter_id=invoice.encounter_id,
            patient_id=invoice.patient_id,
            clinic_id=invoice.clinic_id,
            invoice_number=invoice_number,
            subtotal=subtotal,
            tax=invoice.tax,
            discount=invoice.discount,
            total=total,
            notes=invoice.notes,
            status=invoice.status or 'pending',
            invoice_date=datetime.utcnow()
        )
        
        session.add(new_invoice)
        session.flush()
        
        # Add invoice items
        for item in processed_items:
            invoice_item = InvoiceItem(
                id=str(uuid.uuid4()),
                invoice_id=new_invoice.id,
                item_type=item["item_type"],
                item_name=item["item_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                total=item["total"]
            )
            session.add(invoice_item)
        
        session.commit()
        invoice_id = new_invoice.id
        session.close()
        
        return {
            "status": "success",
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "total": total,
            "message": "Invoice created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, token: str = "demo-token"):
    """Get invoice details"""
    try:
        session = SessionLocal()
        invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            session.close()
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get invoice items
        items = session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
        # Get payments
        payments = session.query(Payment).filter(Payment.invoice_id == invoice_id).all()
        
        session.close()
        
        paid_amount = sum(p.amount for p in payments)
        balance = invoice.total - paid_amount
        
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "patient_id": invoice.patient_id,
            "encounter_id": invoice.encounter_id,
            "clinic_id": invoice.clinic_id,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "subtotal": invoice.subtotal,
            "tax": invoice.tax,
            "discount": invoice.discount,
            "total": invoice.total,
            "paid_amount": paid_amount,
            "balance": balance,
            "status": invoice.status,
            "items": [
                {
                    "item_type": item.item_type,
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total": item.total
                } for item in items
            ],
            "payments": [
                {
                    "amount": p.amount,
                    "payment_method": p.payment_method,
                    "payment_date": p.payment_date.isoformat() if p.payment_date else None
                } for p in payments
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payments")
async def record_payment(payment: PaymentCreate, token: str = "demo-token"):
    """Record a payment for an invoice"""
    try:
        session = SessionLocal()
        
        # Verify invoice exists
        invoice = session.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
        if not invoice:
            session.close()
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Create payment
        new_payment = Payment(
            id=str(uuid.uuid4()),
            invoice_id=payment.invoice_id,
            amount=payment.amount,
            payment_method=payment.payment_method,
            transaction_id=payment.transaction_id,
            notes=payment.notes,
            payment_date=datetime.utcnow()
        )
        
        session.add(new_payment)
        
        # Update invoice status
        total_paid = sum(p.amount for p in session.query(Payment).filter(Payment.invoice_id == payment.invoice_id).all()) + payment.amount
        
        if total_paid >= invoice.total:
            invoice.status = 'paid'
        elif total_paid > 0:
            invoice.status = 'partial'
        
        session.commit()
        payment_id = new_payment.id
        session.close()
        
        return {"status": "success", "payment_id": payment_id, "message": "Payment recorded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
