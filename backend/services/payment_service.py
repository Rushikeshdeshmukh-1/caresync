"""
Payment Service
Handles payment processing with Razorpay integration
"""

import os
import uuid
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text
from models.database import SessionLocal

logger = logging.getLogger(__name__)

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_key")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "webhook_secret")


class PaymentService:
    """Service for handling payments via Razorpay"""
    
    def __init__(self):
        self.key_id = RAZORPAY_KEY_ID
        self.key_secret = RAZORPAY_KEY_SECRET
        self.webhook_secret = RAZORPAY_WEBHOOK_SECRET
        
        # Try to import razorpay client
        try:
            import razorpay
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            self.razorpay_available = True
        except ImportError:
            logger.warning("Razorpay SDK not installed. Payment processing will use mock mode.")
            self.client = None
            self.razorpay_available = False
    
    def create_payment_intent(
        self,
        appointment_id: str,
        patient_id: str,
        amount: float,
        currency: str = "INR",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create payment intent for appointment
        
        Args:
            appointment_id: Appointment ID
            patient_id: Patient ID
            amount: Amount in currency units (e.g., 500.00 for ₹500)
            currency: Currency code
            description: Optional description
            
        Returns:
            Payment intent details
        """
        session = SessionLocal()
        
        try:
            payment_intent_id = str(uuid.uuid4())
            
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount_paise = int(amount * 100)
            
            # Create Razorpay order (if SDK available)
            if self.razorpay_available and self.client:
                try:
                    order_data = {
                        "amount": amount_paise,
                        "currency": currency,
                        "receipt": f"appt_{appointment_id}",
                        "notes": {
                            "appointment_id": appointment_id,
                            "patient_id": patient_id,
                            "payment_intent_id": payment_intent_id
                        }
                    }
                    
                    razorpay_order = self.client.order.create(data=order_data)
                    provider_order_id = razorpay_order['id']
                    
                except Exception as e:
                    logger.error(f"Razorpay order creation error: {str(e)}")
                    provider_order_id = f"mock_order_{uuid.uuid4()}"
            else:
                # Mock mode
                provider_order_id = f"mock_order_{uuid.uuid4()}"
            
            # Create payment intent record
            insert_query = text("""
                INSERT INTO payment_intents
                (id, appointment_id, patient_id, amount, currency, provider,
                 provider_order_id, status, metadata, created_at)
                VALUES
                (:id, :appointment_id, :patient_id, :amount, :currency, :provider,
                 :provider_order_id, :status, :metadata, :created_at)
            """)
            
            import json
            metadata = {
                "description": description or f"Appointment payment",
                "created_by": "payment_service"
            }
            
            session.execute(insert_query, {
                "id": payment_intent_id,
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "amount": amount,
                "currency": currency,
                "provider": "razorpay" if self.razorpay_available else "mock",
                "provider_order_id": provider_order_id,
                "status": "pending",
                "metadata": json.dumps(metadata),
                "created_at": datetime.utcnow()
            })
            
            session.commit()
            
            logger.info(f"Created payment intent {payment_intent_id} for appointment {appointment_id}")
            
            return {
                "payment_intent_id": payment_intent_id,
                "provider_order_id": provider_order_id,
                "amount": amount,
                "currency": currency,
                "status": "pending",
                "razorpay_key_id": self.key_id if self.razorpay_available else None
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating payment intent: {str(e)}")
            raise
        finally:
            session.close()
    
    def verify_payment(
        self,
        payment_intent_id: str,
        provider_payment_id: str,
        provider_order_id: str,
        signature: str
    ) -> Dict[str, Any]:
        """
        Verify payment signature from Razorpay
        
        Args:
            payment_intent_id: Payment intent ID
            provider_payment_id: Razorpay payment ID
            provider_order_id: Razorpay order ID
            signature: Payment signature
            
        Returns:
            Verification result
        """
        session = SessionLocal()
        
        try:
            # Verify signature
            if self.razorpay_available:
                message = f"{provider_order_id}|{provider_payment_id}"
                expected_signature = hmac.new(
                    self.key_secret.encode(),
                    message.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                signature_valid = hmac.compare_digest(signature, expected_signature)
            else:
                # Mock mode - always valid
                signature_valid = True
            
            if not signature_valid:
                raise ValueError("Invalid payment signature")
            
            # Update payment intent
            update_query = text("""
                UPDATE payment_intents
                SET provider_payment_id = :provider_payment_id,
                    status = 'succeeded',
                    paid_at = :paid_at,
                    updated_at = :updated_at
                WHERE id = :payment_intent_id
            """)
            
            now = datetime.utcnow()
            
            session.execute(update_query, {
                "provider_payment_id": provider_payment_id,
                "paid_at": now,
                "updated_at": now,
                "payment_intent_id": payment_intent_id
            })
            
            session.commit()
            
            logger.info(f"Payment verified for intent {payment_intent_id}")
            
            return {
                "status": "succeeded",
                "payment_intent_id": payment_intent_id,
                "verified": True
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Payment verification error: {str(e)}")
            raise
        finally:
            session.close()
    
    def handle_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle Razorpay webhook event
        
        Args:
            event_type: Event type
            payload: Webhook payload
            signature: Webhook signature
            
        Returns:
            Processing result
        """
        session = SessionLocal()
        
        try:
            webhook_id = str(uuid.uuid4())
            
            # Store webhook event
            import json
            insert_query = text("""
                INSERT INTO payment_webhooks
                (id, provider, event_type, payload, signature, processed, created_at)
                VALUES
                (:id, :provider, :event_type, :payload, :signature, :processed, :created_at)
            """)
            
            session.execute(insert_query, {
                "id": webhook_id,
                "provider": "razorpay",
                "event_type": event_type,
                "payload": json.dumps(payload),
                "signature": signature,
                "processed": False,
                "created_at": datetime.utcnow()
            })
            
            session.commit()
            
            # Process event based on type
            if event_type == "payment.captured":
                # Payment successful
                payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
                order_id = payment_entity.get("order_id")
                payment_id = payment_entity.get("id")
                
                # Update payment intent
                if order_id:
                    update_query = text("""
                        UPDATE payment_intents
                        SET provider_payment_id = :payment_id,
                            status = 'succeeded',
                            paid_at = :paid_at
                        WHERE provider_order_id = :order_id
                    """)
                    
                    session.execute(update_query, {
                        "payment_id": payment_id,
                        "paid_at": datetime.utcnow(),
                        "order_id": order_id
                    })
                    
                    session.commit()
            
            elif event_type == "payment.failed":
                # Payment failed
                payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
                order_id = payment_entity.get("order_id")
                error_description = payment_entity.get("error_description", "Payment failed")
                
                if order_id:
                    update_query = text("""
                        UPDATE payment_intents
                        SET status = 'failed',
                            error_message = :error_message
                        WHERE provider_order_id = :order_id
                    """)
                    
                    session.execute(update_query, {
                        "error_message": error_description,
                        "order_id": order_id
                    })
                    
                    session.commit()
            
            # Mark webhook as processed
            mark_processed_query = text("""
                UPDATE payment_webhooks
                SET processed = TRUE
                WHERE id = :webhook_id
            """)
            
            session.execute(mark_processed_query, {"webhook_id": webhook_id})
            session.commit()
            
            return {"status": "processed", "webhook_id": webhook_id}
            
        except Exception as e:
            session.rollback()
            logger.error(f"Webhook processing error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get payment intent status
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            Payment status
        """
        session = SessionLocal()
        
        try:
            query = text("""
                SELECT id, appointment_id, amount, currency, status, 
                       provider_payment_id, paid_at, error_message
                FROM payment_intents
                WHERE id = :payment_intent_id
            """)
            
            result = session.execute(query, {"payment_intent_id": payment_intent_id}).fetchone()
            
            if not result:
                raise ValueError("Payment intent not found")
            
            return {
                "payment_intent_id": result[0],
                "appointment_id": result[1],
                "amount": result[2],
                "currency": result[3],
                "status": result[4],
                "provider_payment_id": result[5],
                "paid_at": result[6].isoformat() if result[6] else None,
                "error_message": result[7]
            }
            
        finally:
            session.close()


# Global service instance
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """Get global payment service instance"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service
