"""
Appointments V2 Service
Business logic for appointment management
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import sqlite3
import uuid
import logging

logger = logging.getLogger(__name__)

class AppointmentsService:
    """Service for managing appointments in V2 schema"""
    
    def __init__(self, db_path: str = "terminology.db"):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        start_time: datetime,
        end_time: datetime,
        reason: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new appointment"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check for conflicts
            conflicts = cursor.execute("""
                SELECT id FROM appointments_v2
                WHERE doctor_id = ?
                AND status NOT IN ('cancelled', 'no_show')
                AND (
                    (start_time <= ? AND end_time > ?)
                    OR (start_time < ? AND end_time >= ?)
                    OR (start_time >= ? AND end_time <= ?)
                )
            """, (doctor_id, start_time, start_time, end_time, end_time, start_time, end_time)).fetchall()
            
            if conflicts:
                raise ValueError("Doctor has conflicting appointment at this time")
            
            # Create appointment
            appointment_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO appointments_v2 
                (id, patient_id, doctor_id, start_time, end_time, 
                 status, reason, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                appointment_id,
                patient_id,
                doctor_id,
                start_time.isoformat(),
                end_time.isoformat(),
                'scheduled',
                reason,
                notes,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            
            # Fetch created appointment
            appointment = cursor.execute("""
                SELECT * FROM appointments_v2 WHERE id = ?
            """, (appointment_id,)).fetchone()
            
            return dict(appointment)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating appointment: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            appointment = cursor.execute("""
                SELECT a.*, 
                       p.name as patient_name,
                       s.user_id as doctor_user_id
                FROM appointments_v2 a
                LEFT JOIN patients p ON a.patient_id = p.id
                LEFT JOIN staff s ON a.doctor_id = s.id
                WHERE a.id = ?
            """, (appointment_id,)).fetchone()
            
            return dict(appointment) if appointment else None
            
        finally:
            conn.close()
    
    def list_appointments(
        self,
        patient_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List appointments with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT a.*, 
                       p.name as patient_name,
                       s.user_id as doctor_user_id
                FROM appointments_v2 a
                LEFT JOIN patients p ON a.patient_id = p.id
                LEFT JOIN staff s ON a.doctor_id = s.id
                WHERE 1=1
            """
            params = []
            
            if patient_id:
                query += " AND a.patient_id = ?"
                params.append(patient_id)
            
            if doctor_id:
                query += " AND a.doctor_id = ?"
                params.append(doctor_id)
            
            if status:
                query += " AND a.status = ?"
                params.append(status)
            
            if from_date:
                query += " AND a.start_time >= ?"
                params.append(from_date.isoformat())
            
            if to_date:
                query += " AND a.start_time <= ?"
                params.append(to_date.isoformat())
            
            query += " ORDER BY a.start_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            appointments = cursor.execute(query, params).fetchall()
            
            return [dict(appt) for appt in appointments]
            
        finally:
            conn.close()
    
    def get_calendar(
        self,
        doctor_id: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get calendar view for a doctor"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            appointments = cursor.execute("""
                SELECT a.id, a.start_time, a.end_time, a.status, a.reason,
                       p.name as patient_name, p.id as patient_id
                FROM appointments_v2 a
                LEFT JOIN patients p ON a.patient_id = p.id
                WHERE a.doctor_id = ?
                AND a.start_time >= ?
                AND a.start_time <= ?
                AND a.status NOT IN ('cancelled')
                ORDER BY a.start_time
            """, (doctor_id, from_date.isoformat(), to_date.isoformat())).fetchall()
            
            return [dict(appt) for appt in appointments]
            
        finally:
            conn.close()
    
    def update_appointment(
        self,
        appointment_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update appointment"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Build update query
            allowed_fields = ['start_time', 'end_time', 'status', 'reason', 'notes']
            update_fields = []
            params = []
            
            for field, value in updates.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = ?")
                    if isinstance(value, datetime):
                        params.append(value.isoformat())
                    else:
                        params.append(value)
            
            if not update_fields:
                raise ValueError("No valid fields to update")
            
            # Add updated_at
            update_fields.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(appointment_id)
            
            query = f"UPDATE appointments_v2 SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            # Fetch updated appointment
            return self.get_appointment(appointment_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating appointment: {str(e)}")
            raise
        finally:
            conn.close()
    
    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Cancel an appointment"""
        return self.update_appointment(appointment_id, status='cancelled')
    
    def delete_appointment(self, appointment_id: str) -> bool:
        """Delete an appointment"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM appointments_v2 WHERE id = ?", (appointment_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting appointment: {str(e)}")
            raise
        finally:
            conn.close()
