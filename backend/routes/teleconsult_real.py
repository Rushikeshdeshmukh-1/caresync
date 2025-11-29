"""
Teleconsult Backend - Real Video Call Logic
Implements actual video meeting functionality using Jitsi Meet
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import jwt
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.database import SessionLocal
from backend.middleware.rbac import get_current_user
from backend.decorators.audit import audit_log

router = APIRouter(prefix="/api/teleconsult", tags=["teleconsult"])

# Jitsi Configuration
JITSI_APP_ID = os.getenv("JITSI_APP_ID", "vpaas-magic-cookie-your-app-id")
JITSI_API_KEY = os.getenv("JITSI_API_KEY", "your-api-key")
JITSI_DOMAIN = "8x8.vc"  # or "meet.jit.si" for free tier

class StartCallRequest(BaseModel):
    appointment_id: str
    participant_name: str

class JoinCallRequest(BaseModel):
    room_id: str
    participant_name: str

class CallResponse(BaseModel):
    room_id: str
    room_url: str
    jwt_token: str
    meeting_started: bool

def generate_jitsi_jwt(room_name: str, user_name: str, is_moderator: bool = False) -> str:
    """
    Generate JWT token for Jitsi Meet authentication
    """
    now = datetime.utcnow()
    
    payload = {
        "aud": "jitsi",
        "iss": JITSI_APP_ID,
        "sub": JITSI_DOMAIN,
        "room": room_name,
        "exp": int((now + timedelta(hours=2)).timestamp()),
        "nbf": int(now.timestamp()),
        "context": {
            "user": {
                "name": user_name,
                "moderator": str(is_moderator).lower(),
                "id": str(uuid.uuid4())
            },
            "features": {
                "livestreaming": "false",
                "recording": "false",
                "transcription": "false"
            }
        }
    }
    
    # For production, use your actual Jitsi API key
    # For development, we'll use a simple token
    token = jwt.encode(payload, JITSI_API_KEY, algorithm="HS256")
    return token

@router.post("/start-call", response_model=CallResponse)
@audit_log
async def start_video_call(
    request: StartCallRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a video call for an appointment
    Doctor initiates the call and gets moderator privileges
    """
    db = SessionLocal()
    
    try:
        # Generate unique room ID
        room_id = f"caresync-{request.appointment_id}-{uuid.uuid4().hex[:8]}"
        
        # Generate Jitsi JWT token (doctor is moderator)
        jwt_token = generate_jitsi_jwt(
            room_name=room_id,
            user_name=request.participant_name,
            is_moderator=True
        )
        
        # Create room URL
        room_url = f"https://{JITSI_DOMAIN}/{room_id}"
        
        # Update appointment with room details
        db.execute("""
            UPDATE appointments 
            SET teleconsult_enabled = 1,
                room_token = ?,
                room_url = ?,
                session_started_at = ?,
                status = 'in-progress'
            WHERE id = ?
        """, (jwt_token, room_url, datetime.utcnow(), request.appointment_id))
        
        db.commit()
        
        return CallResponse(
            room_id=room_id,
            room_url=room_url,
            jwt_token=jwt_token,
            meeting_started=True
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start call: {str(e)}")
    finally:
        db.close()

@router.post("/join-call", response_model=CallResponse)
@audit_log
async def join_video_call(
    request: JoinCallRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Join an existing video call
    Patient joins as participant (not moderator)
    """
    db = SessionLocal()
    
    try:
        # Generate JWT token for participant
        jwt_token = generate_jitsi_jwt(
            room_name=request.room_id,
            user_name=request.participant_name,
            is_moderator=False
        )
        
        # Get room URL
        room_url = f"https://{JITSI_DOMAIN}/{request.room_id}"
        
        return CallResponse(
            room_id=request.room_id,
            room_url=room_url,
            jwt_token=jwt_token,
            meeting_started=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join call: {str(e)}")
    finally:
        db.close()

@router.post("/end-call/{appointment_id}")
@audit_log
async def end_video_call(
    appointment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    End a video call and update appointment status
    """
    db = SessionLocal()
    
    try:
        # Calculate duration
        result = db.execute("""
            SELECT session_started_at FROM appointments WHERE id = ?
        """, (appointment_id,)).fetchone()
        
        if result and result[0]:
            started_at = datetime.fromisoformat(result[0])
            duration = int((datetime.utcnow() - started_at).total_seconds() / 60)
        else:
            duration = 0
        
        # Update appointment
        db.execute("""
            UPDATE appointments 
            SET session_ended_at = ?,
                duration_minutes = ?,
                status = 'completed'
            WHERE id = ?
        """, (datetime.utcnow(), duration, appointment_id))
        
        db.commit()
        
        return {
            "success": True,
            "duration_minutes": duration,
            "message": "Call ended successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to end call: {str(e)}")
    finally:
        db.close()

@router.get("/appointment/{appointment_id}/room-info")
async def get_room_info(
    appointment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get room information for an appointment
    """
    db = SessionLocal()
    
    try:
        result = db.execute("""
            SELECT room_token, room_url, session_started_at, teleconsult_enabled
            FROM appointments 
            WHERE id = ?
        """, (appointment_id,)).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "room_token": result[0],
            "room_url": result[1],
            "session_started_at": result[2],
            "teleconsult_enabled": bool(result[3])
        }
        
    finally:
        db.close()
