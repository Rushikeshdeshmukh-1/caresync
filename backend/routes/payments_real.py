"""
Payment Processing - Real Razorpay Integration
Implements actual payment logic with transaction tracking and revenue updates
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import razorpay
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import SessionLocal
from backend.middleware.rbac import get_current_user
from backend.decorators.audit import audit_log

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_your_key_id")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "your_secret_key")

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

class CreatePaymentRequest(BaseModel):
    appointment_id: str
    amount: float
    currency: str = "INR"
    description: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    appointment_id: str

class PaymentResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    key_id: str
    success: bool

@router.post("/create-order", response_model=PaymentResponse)
@audit_log
async def create_payment_order(
    request: CreatePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a Razorpay payment order
    """
    db = SessionLocal()
    
    try:
        # Create Razorpay order
        amount_in_paise = int(request.amount * 100)  # Convert to paise
        
        order_data = {
            "amount": amount_in_paise,
            "currency": request.currency,
            "receipt": f"apt_{request.appointment_id}",
            "notes": {
                "appointment_id": request.appointment_id,
                "user_id": current_user['id'],
                "description": request.description or "Consultation Payment"
            }
        }
        
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        # Store payment intent in database
        payment_id = str(uuid.uuid4())
        db.execute("""
            INSERT INTO payment_intents 
            (id, user_id, appointment_id, amount, currency, razorpay_order_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payment_id,
            current_user['id'],
            request.appointment_id,
            request.amount,
            request.currency,
            razorpay_order['id'],
            'created',
            datetime.utcnow()
        ))
        
        db.commit()
        
        return PaymentResponse(
            order_id=razorpay_order['id'],
            amount=request.amount,
            currency=request.currency,
            key_id=RAZORPAY_KEY_ID,
            success=True
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create payment order: {str(e)}")
    finally:
        db.close()

@router.post("/verify-payment")
@audit_log
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify Razorpay payment and update database
    """
    db = SessionLocal()
    
    try:
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            payment_verified = True
        except:
            payment_verified = False
            raise HTTPException(status_code=400, detail="Payment verification failed")
        
        # Get payment details
        payment = razorpay_client.payment.fetch(request.razorpay_payment_id)
        
        # Update payment intent
        db.execute("""
            UPDATE payment_intents 
            SET razorpay_payment_id = ?,
                status = 'completed',
                verified_at = ?
            WHERE razorpay_order_id = ?
        """, (
            request.razorpay_payment_id,
            datetime.utcnow(),
            request.razorpay_order_id
        ))
        
        # Get payment amount
        result = db.execute("""
            SELECT amount, user_id FROM payment_intents 
            WHERE razorpay_order_id = ?
        """, (request.razorpay_order_id,)).fetchone()
        
        if result:
            amount, patient_id = result
            
            # Get doctor ID from appointment
            doctor_result = db.execute("""
                SELECT staff_id FROM appointments WHERE id = ?
            """, (request.appointment_id,)).fetchone()
            
            if doctor_result:
                doctor_id = doctor_result[0]
                
                # Create transaction record
                transaction_id = str(uuid.uuid4())
                db.execute("""
                    INSERT INTO transactions 
                    (id, payment_id, patient_id, doctor_id, amount, type, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_id,
                    request.razorpay_payment_id,
                    patient_id,
                    doctor_id,
                    amount,
                    'consultation',
                    'completed',
                    datetime.utcnow()
                ))
                
                # Update doctor revenue
                db.execute("""
                    INSERT INTO doctor_revenue (doctor_id, total_revenue, last_updated)
                    VALUES (?, ?, ?)
                    ON CONFLICT(doctor_id) DO UPDATE SET
                        total_revenue = total_revenue + ?,
                        last_updated = ?
                """, (
                    doctor_id,
                    amount,
                    datetime.utcnow(),
                    amount,
                    datetime.utcnow()
                ))
                
                # Update appointment status to paid
                db.execute("""
                    UPDATE appointments 
                    SET status = 'paid'
                    WHERE id = ?
                """, (request.appointment_id,))
        
        db.commit()
        
        return {
            "success": True,
            "payment_id": request.razorpay_payment_id,
            "status": "completed",
            "message": "Payment verified and processed successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to verify payment: {str(e)}")
    finally:
        db.close()

@router.get("/history")
@audit_log
async def get_payment_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Get payment history for current user
    """
    db = SessionLocal()
    
    try:
        # Get payments for this user
        results = db.execute("""
            SELECT 
                pi.id,
                pi.amount,
                pi.currency,
                pi.status,
                pi.created_at,
                pi.razorpay_payment_id,
                a.appointment_date
            FROM payment_intents pi
            LEFT JOIN appointments a ON pi.appointment_id = a.id
            WHERE pi.user_id = ?
            ORDER BY pi.created_at DESC
        """, (current_user['id'],)).fetchall()
        
        payments = []
        for row in results:
            payments.append({
                "id": row[0],
                "amount": row[1],
                "currency": row[2],
                "status": row[3],
                "created_at": row[4],
                "payment_id": row[5],
                "appointment_date": row[6],
                "description": "Consultation Payment",
                "method": "Razorpay"
            })
        
        return {"payments": payments}
        
    finally:
        db.close()

@router.get("/revenue")
@audit_log
async def get_doctor_revenue(
    current_user: dict = Depends(get_current_user)
):
    """
    Get revenue statistics for doctor
    """
    if current_user['role'] not in ['doctor', 'admin']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db = SessionLocal()
    
    try:
        result = db.execute("""
            SELECT total_revenue, last_updated
            FROM doctor_revenue
            WHERE doctor_id = ?
        """, (current_user['id'],)).fetchone()
        
        if result:
            return {
                "total_revenue": result[0],
                "last_updated": result[1]
            }
        else:
            return {
                "total_revenue": 0.0,
                "last_updated": None
            }
        
    finally:
        db.close()
