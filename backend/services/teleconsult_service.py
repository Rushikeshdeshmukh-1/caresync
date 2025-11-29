"""
Teleconsult Service
Handles video consultation room creation and management using Jitsi
"""

import os
import jwt
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import text
from models.database import SessionLocal

logger = logging.getLogger(__name__)

# Jitsi Configuration
JITSI_DOMAIN = os.getenv("JITSI_DOMAIN", "meet.jit.si")  # Use public Jitsi or self-hosted
JITSI_APP_ID = os.getenv("JITSI_APP_ID", "caresync")
JITSI_SECRET = os.getenv("JITSI_SECRET", "your-jitsi-secret-key")  # For JWT signing


class TeleconsultService:
    """Service for managing teleconsult video sessions"""
    
    def __init__(self):
        self.jitsi_domain = JITSI_DOMAIN
        self.app_id = JITSI_APP_ID
        self.secret = JITSI_SECRET
    
    def generate_room_name(self, appointment_id: str) -> str:
        """
        Generate unique room name for appointment
        
        Args:
            appointment_id: Appointment ID
            
        Returns:
            Room name
        """
        # Create readable but unique room name
        room_id = str(uuid.uuid4())[:8]
        return f"caresync-{appointment_id}-{room_id}"
    
    def create_jitsi_token(
        self,
        room_name: str,
        user_id: str,
        user_name: str,
        is_moderator: bool = False,
        avatar_url: Optional[str] = None
    ) -> str:
        """
        Create JWT token for Jitsi room access
        
        Args:
            room_name: Room name
            user_id: User ID
            user_name: Display name
            is_moderator: Whether user is moderator (doctor)
            avatar_url: Optional avatar URL
            
        Returns:
            JWT token for Jitsi
        """
        now = datetime.utcnow()
        expire = now + timedelta(hours=2)  # 2 hour session
        
        payload = {
            "iss": self.app_id,
            "aud": self.app_id,
            "exp": int(expire.timestamp()),
            "nbf": int(now.timestamp()),
            "room": room_name,
            "context": {
                "user": {
                    "id": user_id,
                    "name": user_name,
                    "avatar": avatar_url or "",
                    "moderator": is_moderator
                }
            }
        }
        
        token = jwt.encode(payload, self.secret, algorithm="HS256")
        return token
    
    def create_room(
        self,
        appointment_id: str,
        host_user_id: str,
        host_name: str
    ) -> Dict[str, Any]:
        """
        Create teleconsult room for appointment
        
        Args:
            appointment_id: Appointment ID
            host_user_id: Doctor user ID
            host_name: Doctor name
            
        Returns:
            Dict with room details
        """
        session = SessionLocal()
        
        try:
            # Generate room name
            room_name = self.generate_room_name(appointment_id)
            
            # Create host token (moderator)
            host_token = self.create_jitsi_token(
                room_name=room_name,
                user_id=host_user_id,
                user_name=host_name,
                is_moderator=True
            )
            
            # Build room URL
            room_url = f"https://{self.jitsi_domain}/{room_name}"
            
            # Create teleconsult session record
            session_id = str(uuid.uuid4())
            
            insert_query = text("""
                INSERT INTO teleconsult_sessions 
                (id, appointment_id, room_name, room_token, host_user_id, 
                 participant_user_ids, status, created_at)
                VALUES 
                (:id, :appointment_id, :room_name, :room_token, :host_user_id,
                 :participant_user_ids, :status, :created_at)
            """)
            
            session.execute(insert_query, {
                "id": session_id,
                "appointment_id": appointment_id,
                "room_name": room_name,
                "room_token": host_token,
                "host_user_id": host_user_id,
                "participant_user_ids": "[]",
                "status": "scheduled",
                "created_at": datetime.utcnow()
            })
            
            # Update appointment with room details
            update_query = text("""
                UPDATE appointments 
                SET teleconsult_enabled = TRUE,
                    room_token = :room_token,
                    room_url = :room_url
                WHERE id = :appointment_id
            """)
            
            session.execute(update_query, {
                "room_token": host_token,
                "room_url": room_url,
                "appointment_id": appointment_id
            })
            
            session.commit()
            
            logger.info(f"Created teleconsult room for appointment {appointment_id}")
            
            return {
                "session_id": session_id,
                "room_name": room_name,
                "room_url": room_url,
                "host_token": host_token,
                "join_url": f"{room_url}?jwt={host_token}"
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating teleconsult room: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_participant_token(
        self,
        appointment_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Get participant token for joining room
        
        Args:
            appointment_id: Appointment ID
            user_id: Participant user ID
            user_name: Participant name
            
        Returns:
            Dict with join details
        """
        session = SessionLocal()
        
        try:
            # Get teleconsult session
            query = text("""
                SELECT room_name, room_token, status
                FROM teleconsult_sessions
                WHERE appointment_id = :appointment_id
            """)
            
            result = session.execute(query, {"appointment_id": appointment_id}).fetchone()
            
            if not result:
                raise ValueError("Teleconsult session not found")
            
            room_name, host_token, status = result
            
            # Create participant token
            participant_token = self.create_jitsi_token(
                room_name=room_name,
                user_id=user_id,
                user_name=user_name,
                is_moderator=False
            )
            
            room_url = f"https://{self.jitsi_domain}/{room_name}"
            
            return {
                "room_name": room_name,
                "room_url": room_url,
                "participant_token": participant_token,
                "join_url": f"{room_url}?jwt={participant_token}",
                "status": status
            }
            
        finally:
            session.close()
    
    def start_session(self, appointment_id: str) -> Dict[str, Any]:
        """
        Mark session as started
        
        Args:
            appointment_id: Appointment ID
            
        Returns:
            Updated session details
        """
        session = SessionLocal()
        
        try:
            now = datetime.utcnow()
            
            # Update teleconsult session
            update_session_query = text("""
                UPDATE teleconsult_sessions
                SET status = 'active',
                    started_at = :started_at
                WHERE appointment_id = :appointment_id
            """)
            
            session.execute(update_session_query, {
                "started_at": now,
                "appointment_id": appointment_id
            })
            
            # Update appointment
            update_appt_query = text("""
                UPDATE appointments
                SET session_started_at = :started_at,
                    status = 'in_progress'
                WHERE id = :appointment_id
            """)
            
            session.execute(update_appt_query, {
                "started_at": now,
                "appointment_id": appointment_id
            })
            
            session.commit()
            
            logger.info(f"Started teleconsult session for appointment {appointment_id}")
            
            return {"status": "active", "started_at": now.isoformat()}
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error starting session: {str(e)}")
            raise
        finally:
            session.close()
    
    def end_session(self, appointment_id: str) -> Dict[str, Any]:
        """
        End teleconsult session
        
        Args:
            appointment_id: Appointment ID
            
        Returns:
            Session summary
        """
        session = SessionLocal()
        
        try:
            now = datetime.utcnow()
            
            # Get session start time
            query = text("""
                SELECT started_at FROM teleconsult_sessions
                WHERE appointment_id = :appointment_id
            """)
            
            result = session.execute(query, {"appointment_id": appointment_id}).fetchone()
            
            if not result or not result[0]:
                raise ValueError("Session not started")
            
            started_at = result[0]
            duration = int((now - started_at).total_seconds())
            
            # Update teleconsult session
            update_session_query = text("""
                UPDATE teleconsult_sessions
                SET status = 'ended',
                    ended_at = :ended_at,
                    duration_seconds = :duration
                WHERE appointment_id = :appointment_id
            """)
            
            session.execute(update_session_query, {
                "ended_at": now,
                "duration": duration,
                "appointment_id": appointment_id
            })
            
            # Update appointment
            update_appt_query = text("""
                UPDATE appointments
                SET session_ended_at = :ended_at,
                    duration_minutes = :duration_minutes,
                    status = 'completed'
                WHERE id = :appointment_id
            """)
            
            session.execute(update_appt_query, {
                "ended_at": now,
                "duration_minutes": duration // 60,
                "appointment_id": appointment_id
            })
            
            session.commit()
            
            logger.info(f"Ended teleconsult session for appointment {appointment_id}, duration: {duration}s")
            
            return {
                "status": "ended",
                "ended_at": now.isoformat(),
                "duration_seconds": duration,
                "duration_minutes": duration // 60
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error ending session: {str(e)}")
            raise
        finally:
            session.close()


# Global service instance
_teleconsult_service: Optional[TeleconsultService] = None


def get_teleconsult_service() -> TeleconsultService:
    """Get global teleconsult service instance"""
    global _teleconsult_service
    if _teleconsult_service is None:
        _teleconsult_service = TeleconsultService()
    return _teleconsult_service
