"""
Teleconsult Routes - Add to main.py
Simple implementation for video consultations
"""

# Add these imports at the top of main.py
from datetime import datetime
import uuid
import jwt as pyjwt

# Add these routes to main.py

@app.get("/api/teleconsult/appointments")
async def get_teleconsult_appointments(request: FastAPIRequest):
    """Get appointments for teleconsult"""
    try:
        # Get user from token (simplified for now)
        auth_header = request.headers.get("Authorization", "")
        
        db = get_db()
        
        # Get all scheduled appointments with teleconsult enabled
        query = """
            SELECT 
                a.id,
                a.patient_id,
                a.staff_id,
                a.appointment_date,
                a.appointment_time,
                a.status,
                a.reason,
                a.notes,
                a.room_url,
                a.teleconsult_enabled,
                u1.name as patient_name,
                u2.name as doctor_name
            FROM appointments a
            LEFT JOIN users u1 ON a.patient_id = u1.id
            LEFT JOIN users u2 ON a.staff_id = u2.id
            WHERE a.teleconsult_enabled = 1
            AND a.status IN ('scheduled', 'in-progress')
            ORDER BY a.appointment_date, a.appointment_time
        """
        
        results = db.execute(query).fetchall()
        
        appointments = []
        for row in results:
            appointments.append({
                "id": row[0],
                "patient_id": row[1],
                "staff_id": row[2],
                "date": row[3],
                "time": row[4],
                "status": row[5],
                "reason": row[6],
                "notes": row[7],
                "room_url": row[8],
                "teleconsult_enabled": bool(row[9]),
                "patient_name": row[10] or "Unknown Patient",
                "doctor_name": row[11] or "Unknown Doctor"
            })
        
        return {"appointments": appointments}
        
    except Exception as e:
        logger.error(f"Error fetching teleconsult appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/teleconsult/start-call")
async def start_teleconsult_call(request: FastAPIRequest):
    """Start a teleconsult video call"""
    try:
        data = await request.json()
        appointment_id = data.get("appointment_id")
        participant_name = data.get("participant_name", "User")
        
        # Generate unique room ID
        room_id = f"caresync-{appointment_id}-{uuid.uuid4().hex[:8]}"
        
        # For demo, create a simple JWT (in production, use proper Jitsi JWT)
        jwt_token = f"demo-token-{uuid.uuid4().hex[:16]}"
        
        # Create room URL
        room_url = f"https://meet.jit.si/{room_id}"
        
        # Update appointment
        db = get_db()
        db.execute("""
            UPDATE appointments 
            SET room_token = ?,
                room_url = ?,
                session_started_at = ?,
                status = 'in-progress'
            WHERE id = ?
        """, (jwt_token, room_url, datetime.utcnow(), appointment_id))
        
        db.commit()
        
        return {
            "room_id": room_id,
            "room_url": room_url,
            "jwt_token": jwt_token,
            "meeting_started": True
        }
        
    except Exception as e:
        logger.error(f"Error starting teleconsult: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/teleconsult/join-call")
async def join_teleconsult_call(request: FastAPIRequest):
    """Join an existing teleconsult call"""
    try:
        data = await request.json()
        room_id = data.get("room_id")
        participant_name = data.get("participant_name", "User")
        
        # Generate JWT for participant
        jwt_token = f"demo-token-{uuid.uuid4().hex[:16]}"
        
        # Get room URL
        room_url = f"https://meet.jit.si/{room_id}"
        
        return {
            "room_id": room_id,
            "room_url": room_url,
            "jwt_token": jwt_token,
            "meeting_started": True
        }
        
    except Exception as e:
        logger.error(f"Error joining teleconsult: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/teleconsult/end-call/{appointment_id}")
async def end_teleconsult_call(appointment_id: str):
    """End a teleconsult call"""
    try:
        db = get_db()
        
        # Get session start time
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
        logger.error(f"Error ending teleconsult: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
