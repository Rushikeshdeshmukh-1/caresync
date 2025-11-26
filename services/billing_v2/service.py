"""
Billing V2 Service
Business logic for billing and invoice management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import sqlite3
import uuid
import logging

logger = logging.getLogger(__name__)

class BillingService:
    """Service for managing bills in V2 schema"""
    
    def __init__(self, db_path: str = "terminology.db"):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_bill(
        self,
        patient_id: str,
        appointment_id: Optional[str] = None,
        prescription_id: Optional[str] = None,
        items: List[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new bill with items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculate total amount
            total_amount = sum(item.get('amount', 0) for item in (items or []))
            
            # Create bill
            bill_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO bills_v2 
                (id, patient_id, appointment_id, prescription_id, total_amount, 
                 paid_amount, payment_status, payment_method, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bill_id,
                patient_id,
                appointment_id,
                prescription_id,
                total_amount,
                0,  # paid_amount starts at 0
                'unpaid',
                None,
                notes,
                datetime.utcnow().isoformat()
            ))
            
            # Create bill items
            if items:
                for item in items:
                    item_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO bill_items_v2 
                        (id, bill_id, description, quantity, unit_price, amount, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item_id,
                        bill_id,
                        item.get('description'),
                        item.get('quantity', 1),
                        item.get('unit_price', 0),
                        item.get('amount', 0),
                        datetime.utcnow().isoformat()
                    ))
            
            conn.commit()
            
            # Fetch created bill with items
            return self.get_bill(bill_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating bill: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_bill(self, bill_id: str) -> Optional[Dict[str, Any]]:
        """Get bill by ID with items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            bill = cursor.execute("""
                SELECT b.*, 
                       p.name as patient_name
                FROM bills_v2 b
                LEFT JOIN patients p ON b.patient_id = p.id
                WHERE b.id = ?
            """, (bill_id,)).fetchone()
            
            if not bill:
                return None
            
            # Get bill items
            items = cursor.execute("""
                SELECT * FROM bill_items_v2
                WHERE bill_id = ?
                ORDER BY created_at
            """, (bill_id,)).fetchall()
            
            result = dict(bill)
            result['items'] = [dict(item) for item in items]
            
            return result
            
        finally:
            conn.close()
    
    def list_bills(
        self,
        patient_id: Optional[str] = None,
        payment_status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List bills with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT b.*, 
                       p.name as patient_name,
                       COUNT(bi.id) as item_count
                FROM bills_v2 b
                LEFT JOIN patients p ON b.patient_id = p.id
                LEFT JOIN bill_items_v2 bi ON b.id = bi.bill_id
                WHERE 1=1
            """
            params = []
            
            if patient_id:
                query += " AND b.patient_id = ?"
                params.append(patient_id)
            
            if payment_status:
                query += " AND b.payment_status = ?"
                params.append(payment_status)
            
            if from_date:
                query += " AND b.created_at >= ?"
                params.append(from_date.isoformat())
            
            if to_date:
                query += " AND b.created_at <= ?"
                params.append(to_date.isoformat())
            
            query += " GROUP BY b.id ORDER BY b.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            bills = cursor.execute(query, params).fetchall()
            
            return [dict(bill) for bill in bills]
            
        finally:
            conn.close()
    
    def update_payment(
        self,
        bill_id: str,
        paid_amount: float,
        payment_method: Optional[str] = None,
        payment_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update payment information"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current bill
            bill = self.get_bill(bill_id)
            if not bill:
                raise ValueError("Bill not found")
            
            # Determine payment status if not provided
            if payment_status is None:
                total = bill['total_amount']
                if paid_amount >= total:
                    payment_status = 'paid'
                elif paid_amount > 0:
                    payment_status = 'partial'
                else:
                    payment_status = 'unpaid'
            
            cursor.execute("""
                UPDATE bills_v2 
                SET paid_amount = ?, 
                    payment_method = ?, 
                    payment_status = ?,
                    payment_date = ?
                WHERE id = ?
            """, (
                paid_amount,
                payment_method,
                payment_status,
                datetime.utcnow().isoformat() if paid_amount > 0 else None,
                bill_id
            ))
            
            conn.commit()
            
            return self.get_bill(bill_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating payment: {str(e)}")
            raise
        finally:
            conn.close()
    
    def delete_bill(self, bill_id: str) -> bool:
        """Delete a bill and its items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM bills_v2 WHERE id = ?", (bill_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting bill: {str(e)}")
            raise
        finally:
            conn.close()
