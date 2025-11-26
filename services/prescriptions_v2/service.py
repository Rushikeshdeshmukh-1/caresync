"""
Prescriptions V2 Service
Business logic for prescription management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import sqlite3
import uuid
import logging

logger = logging.getLogger(__name__)

class PrescriptionsService:
    """Service for managing prescriptions in V2 schema"""
    
    def __init__(self, db_path: str = "terminology.db"):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_prescription(
        self,
        patient_id: str,
        doctor_id: str,
        appointment_id: Optional[str] = None,
        diagnosis: Optional[str] = None,
        notes: Optional[str] = None,
        items: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new prescription with items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create prescription
            prescription_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO prescriptions_v2 
                (id, patient_id, doctor_id, appointment_id, issued_at, diagnosis, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prescription_id,
                patient_id,
                doctor_id,
                appointment_id,
                datetime.utcnow().isoformat(),
                diagnosis,
                notes,
                datetime.utcnow().isoformat()
            ))
            
            # Create prescription items
            if items:
                for item in items:
                    item_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO prescription_items_v2 
                        (id, prescription_id, medicine_name, form, dose, frequency, duration, instructions, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item_id,
                        prescription_id,
                        item.get('medicine_name'),
                        item.get('form'),
                        item.get('dose'),
                        item.get('frequency'),
                        item.get('duration'),
                        item.get('instructions'),
                        datetime.utcnow().isoformat()
                    ))
            
            conn.commit()
            
            # Fetch created prescription with items
            return self.get_prescription(prescription_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating prescription: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_prescription(self, prescription_id: str) -> Optional[Dict[str, Any]]:
        """Get prescription by ID with items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            prescription = cursor.execute("""
                SELECT p.*, 
                       pt.name as patient_name,
                       s.user_id as doctor_user_id
                FROM prescriptions_v2 p
                LEFT JOIN patients pt ON p.patient_id = pt.id
                LEFT JOIN staff s ON p.doctor_id = s.id
                WHERE p.id = ?
            """, (prescription_id,)).fetchone()
            
            if not prescription:
                return None
            
            # Get prescription items
            items = cursor.execute("""
                SELECT * FROM prescription_items_v2
                WHERE prescription_id = ?
                ORDER BY created_at
            """, (prescription_id,)).fetchall()
            
            result = dict(prescription)
            result['items'] = [dict(item) for item in items]
            
            return result
            
        finally:
            conn.close()
    
    def list_prescriptions(
        self,
        patient_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        appointment_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List prescriptions with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT p.*, 
                       pt.name as patient_name,
                       s.user_id as doctor_user_id,
                       COUNT(pi.id) as item_count
                FROM prescriptions_v2 p
                LEFT JOIN patients pt ON p.patient_id = pt.id
                LEFT JOIN staff s ON p.doctor_id = s.id
                LEFT JOIN prescription_items_v2 pi ON p.id = pi.prescription_id
                WHERE 1=1
            """
            params = []
            
            if patient_id:
                query += " AND p.patient_id = ?"
                params.append(patient_id)
            
            if doctor_id:
                query += " AND p.doctor_id = ?"
                params.append(doctor_id)
            
            if appointment_id:
                query += " AND p.appointment_id = ?"
                params.append(appointment_id)
            
            if from_date:
                query += " AND p.issued_at >= ?"
                params.append(from_date.isoformat())
            
            if to_date:
                query += " AND p.issued_at <= ?"
                params.append(to_date.isoformat())
            
            query += " GROUP BY p.id ORDER BY p.issued_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            prescriptions = cursor.execute(query, params).fetchall()
            
            return [dict(pres) for pres in prescriptions]
            
        finally:
            conn.close()
    
    def update_prescription(
        self,
        prescription_id: str,
        diagnosis: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update prescription"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if diagnosis is not None:
                updates.append("diagnosis = ?")
                params.append(diagnosis)
            
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            
            if not updates:
                raise ValueError("No fields to update")
            
            params.append(prescription_id)
            query = f"UPDATE prescriptions_v2 SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            return self.get_prescription(prescription_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating prescription: {str(e)}")
            raise
        finally:
            conn.close()
    
    def delete_prescription(self, prescription_id: str) -> bool:
        """Delete a prescription and its items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM prescriptions_v2 WHERE id = ?", (prescription_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting prescription: {str(e)}")
            raise
        finally:
            conn.close()
