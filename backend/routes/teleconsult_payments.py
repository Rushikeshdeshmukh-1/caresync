"""
Teleconsult & Payment Routes
Handles teleconsult session management and payment processing
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from backend.services.teleconsult_service import get_teleconsult_service
from backend.services.payment_service import get_payment_service
from backend.middleware.rbac import require_auth, require_role, ActorContext, Roles
from backend.decorators.audit import audit_create, audit_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["teleconsult", "payments"])


# ==================== Teleconsult Models ====================

class CreateRoomRequest(BaseModel):
    appointment_id: str
    host_name: str


class JoinRoomRequest(BaseModel):
    appointment_id: str
    user_name: str


class SessionActionRequest(BaseModel):
    appointment_id: str


# ==================== Payment Models ====================

class CreatePaymentRequest(BaseModel):
    appointment_id: str
    patient_id: str
    amount: float
    currency: str = "INR"
    description: Optional[str] = None


class VerifyPaymentRequest(BaseModel):
    payment_intent_id: str
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


# ==================== Teleconsult Routes ====================

@router.post("/teleconsult/create-room")
@audit_create(resource="teleconsult_session", extract_id=lambda r: r.get('session_id'))
async def create_teleconsult_room(
    request: Request,
    data: CreateRoomRequest,
    actor: ActorContext = Depends(require_role(Roles.DOCTOR))
):
    """
    Create teleconsult room for appointment (Doctor only)
    
    Returns room URL and JWT token for Jitsi
    """
    try:
        teleconsult_service = get_teleconsult_service()
        
        result = teleconsult_service.create_room(
            appointment_id=data.appointment_id,
            host_user_id=actor.actor_id,
            host_name=data.host_name
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating teleconsult room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teleconsult/join-room")
async def join_teleconsult_room(
    data: JoinRoomRequest,
    actor: ActorContext = Depends(require_auth)
):
    """
    Get participant token to join teleconsult room
    
    Returns join URL with JWT token
    """
    try:
        teleconsult_service = get_teleconsult_service()
        
        result = teleconsult_service.get_participant_token(
            appointment_id=data.appointment_id,
            user_id=actor.actor_id,
            user_name=data.user_name
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error joining teleconsult room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teleconsult/start-session")
@audit_action(resource="teleconsult_session", action="start")
async def start_teleconsult_session(
    request: Request,
    data: SessionActionRequest,
    actor: ActorContext = Depends(require_role(Roles.DOCTOR))
):
    """
    Start teleconsult session (Doctor only)
    
    Marks session as active and records start time
    """
    try:
        teleconsult_service = get_teleconsult_service()
        
        result = teleconsult_service.start_session(data.appointment_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teleconsult/end-session")
@audit_action(resource="teleconsult_session", action="end")
async def end_teleconsult_session(
    request: Request,
    data: SessionActionRequest,
    actor: ActorContext = Depends(require_role(Roles.DOCTOR))
):
    """
    End teleconsult session (Doctor only)
    
    Records end time and calculates duration
    """
    try:
        teleconsult_service = get_teleconsult_service()
        
        result = teleconsult_service.end_session(data.appointment_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Payment Routes ====================

@router.post("/payments/create")
@audit_create(resource="payment_intent", extract_id=lambda r: r.get('payment_intent_id'))
async def create_payment(
    request: Request,
    data: CreatePaymentRequest,
    actor: ActorContext = Depends(require_auth)
):
    """
    Create payment intent for appointment
    
    Returns Razorpay order details for checkout
    """
    try:
        payment_service = get_payment_service()
        
        result = payment_service.create_payment_intent(
            appointment_id=data.appointment_id,
            patient_id=data.patient_id,
            amount=data.amount,
            currency=data.currency,
            description=data.description
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payments/verify")
@audit_action(resource="payment_intent", action="verify")
async def verify_payment(
    request: Request,
    data: VerifyPaymentRequest,
    actor: ActorContext = Depends(require_auth)
):
    """
    Verify payment after Razorpay checkout
    
    Validates payment signature and updates status
    """
    try:
        payment_service = get_payment_service()
        
        result = payment_service.verify_payment(
            payment_intent_id=data.payment_intent_id,
            provider_payment_id=data.razorpay_payment_id,
            provider_order_id=data.razorpay_order_id,
            signature=data.razorpay_signature
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payments/webhook")
async def payment_webhook(request: Request):
    """
    Handle Razorpay webhook events
    
    Processes payment status updates from Razorpay
    """
    try:
        # Get webhook payload
        payload = await request.json()
        signature = request.headers.get("X-Razorpay-Signature", "")
        event_type = payload.get("event", "")
        
        payment_service = get_payment_service()
        
        result = payment_service.handle_webhook(
            event_type=event_type,
            payload=payload,
            signature=signature
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/{payment_intent_id}")
async def get_payment_status(
    payment_intent_id: str,
    actor: ActorContext = Depends(require_auth)
):
    """
    Get payment intent status
    
    Returns current payment status and details
    """
    try:
        payment_service = get_payment_service()
        
        result = payment_service.get_payment_status(payment_intent_id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
