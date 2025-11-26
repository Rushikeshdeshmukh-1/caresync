"""
Dashboard and Analytics API Routes
Updated to use V2 tables with real-time data (no dummy data)
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import sqlite3
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect("terminology.db")
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/stats")
async def get_dashboard_stats(clinic_id: Optional[str] = None, token: str = "demo-token"):
    """Get dashboard statistics from V2 tables (real-time data only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Today's date
        today = datetime.utcnow().date().isoformat()
        
        # Total patients (from patients table - unchanged)
        total_patients = cursor.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        
        # Today's appointments from V2 table
        today_appointments = cursor.execute("""
            SELECT COUNT(*) FROM appointments_v2
            WHERE DATE(start_time) = ?
        """, (today,)).fetchone()[0]
        
        # Today's encounters (from encounters table - unchanged)
        today_encounters = cursor.execute("""
            SELECT COUNT(*) FROM encounters
            WHERE DATE(visit_date) = ?
        """, (today,)).fetchone()[0]
        
        # Today's revenue from V2 bills table
        today_revenue = cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM bills_v2
            WHERE DATE(created_at) = ? AND status = 'paid'
        """, (today,)).fetchone()[0]
        
        # Pending appointments from V2 table
        pending_appointments = cursor.execute("""
            SELECT COUNT(*) FROM appointments_v2
            WHERE status = 'scheduled'
        """).fetchone()[0]
        
        # Active prescriptions from V2 table
        active_prescriptions = cursor.execute("""
            SELECT COUNT(*) FROM prescriptions_v2
            WHERE DATE(issued_at) >= DATE('now', '-30 days')
        """).fetchone()[0]
        
        # Unpaid bills from V2 table
        unpaid_bills = cursor.execute("""
            SELECT COUNT(*) FROM bills_v2
            WHERE status IN ('unpaid', 'partial')
        """).fetchone()[0]
        
        conn.close()
        
        return {
            "total_patients": total_patients,
            "today_appointments": today_appointments,
            "today_encounters": today_encounters,
            "today_revenue": float(today_revenue),
            "pending_appointments": pending_appointments,
            "active_prescriptions": active_prescriptions,
            "unpaid_bills": unpaid_bills,
            "data_source": "v2_tables_realtime"
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics(
    clinic_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: str = "demo-token"
):
    """Get analytics data from V2 tables (real-time data only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Parse dates
        start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end = datetime.utcnow().isoformat()
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).isoformat()
            except:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).isoformat()
            except:
                pass
        
        # Appointments by date from V2 table
        appointments_by_date = cursor.execute("""
            SELECT DATE(start_time) as date, COUNT(*) as count
            FROM appointments_v2
            WHERE start_time >= ? AND start_time <= ?
            GROUP BY DATE(start_time)
            ORDER BY date
        """, (start, end)).fetchall()
        
        # Revenue by date from V2 bills table
        revenue_by_date = cursor.execute("""
            SELECT DATE(created_at) as date, SUM(total_amount) as total
            FROM bills_v2
            WHERE created_at >= ? AND created_at <= ? AND status = 'paid'
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start, end)).fetchall()
        
        # Prescriptions by date from V2 table
        prescriptions_by_date = cursor.execute("""
            SELECT DATE(issued_at) as date, COUNT(*) as count
            FROM prescriptions_v2
            WHERE issued_at >= ? AND issued_at <= ?
            GROUP BY DATE(issued_at)
            ORDER BY date
        """, (start, end)).fetchall()
        
        # Top diagnoses (from encounter diagnoses - unchanged)
        top_diagnoses = cursor.execute("""
            SELECT icd_code, COUNT(*) as count
            FROM encounter_diagnoses
            WHERE created_at >= ?
            GROUP BY icd_code
            ORDER BY count DESC
            LIMIT 10
        """, (start,)).fetchall()
        
        # Appointment status distribution from V2 table
        appointment_status = cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM appointments_v2
            WHERE start_time >= ? AND start_time <= ?
            GROUP BY status
        """, (start, end)).fetchall()
        
        # Payment methods from V2 payments table
        payment_methods = cursor.execute("""
            SELECT method, COUNT(*) as count, SUM(amount) as total
            FROM payments_v2
            WHERE payment_date >= ? AND payment_date <= ?
            GROUP BY method
        """, (start, end)).fetchall()
        
        conn.close()
        
        return {
            "period": {
                "start": start,
                "end": end
            },
            "appointments_by_date": [
                {"date": row['date'], "count": row['count']} for row in appointments_by_date
            ],
            "revenue_by_date": [
                {"date": row['date'], "total": float(row['total'] or 0)} for row in revenue_by_date
            ],
            "prescriptions_by_date": [
                {"date": row['date'], "count": row['count']} for row in prescriptions_by_date
            ],
            "top_diagnoses": [
                {"icd_code": row['icd_code'], "count": row['count']} for row in top_diagnoses
            ],
            "appointment_status": [
                {"status": row['status'], "count": row['count']} for row in appointment_status
            ],
            "payment_methods": [
                {"method": row['method'], "count": row['count'], "total": float(row['total'] or 0)} 
                for row in payment_methods
            ],
            "data_source": "v2_tables_realtime"
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
