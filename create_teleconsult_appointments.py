"""
Create Sample Appointments for Teleconsult Testing
Creates realistic appointments that will appear on the Teleconsult page
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
import random

def create_teleconsult_appointments():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    print("Creating sample appointments for Teleconsult...\n")
    
    # Get users
    users = cursor.execute("SELECT id, name, role FROM users").fetchall()
    doctors = [u for u in users if u[2] == 'doctor']
    patients = [u for u in users if u[2] == 'patient']
    
    if not doctors:
        print("✗ No doctor users found. Please create a doctor account first.")
        return
    
    if not patients:
        print("✗ No patient users found. Please create a patient account first.")
        return
    
    doctor = doctors[0]
    patient = patients[0] if patients else None
    
    print(f"Doctor: {doctor[1]} ({doctor[0]})")
    print(f"Patient: {patient[1] if patient else 'None'} ({patient[0] if patient else 'N/A'})\n")
    
    # Create appointments for different scenarios
    appointments = [
        {
            'date': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d'),
            'time': (datetime.now() + timedelta(hours=2)).strftime('%I:%M %p'),
            'status': 'scheduled',
            'reason': 'Follow-up Video Consultation',
            'notes': 'Patient requested video call for follow-up'
        },
        {
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '10:00 AM',
            'status': 'scheduled',
            'reason': 'Initial Consultation - Teleconsult',
            'notes': 'New patient consultation via video'
        },
        {
            'date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'time': '02:00 PM',
            'status': 'scheduled',
            'reason': 'Prescription Review',
            'notes': 'Review current medications via video call'
        },
        {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': (datetime.now() + timedelta(minutes=30)).strftime('%I:%M %p'),
            'status': 'scheduled',
            'reason': 'Urgent Consultation',
            'notes': 'Patient needs immediate consultation'
        }
    ]
    
    created_count = 0
    
    for apt_data in appointments:
        apt_id = str(uuid.uuid4())
        
        try:
            cursor.execute("""
                INSERT INTO appointments 
                (id, patient_id, staff_id, clinic_id, department_id,
                 appointment_date, appointment_time, status, reason, notes,
                 teleconsult_enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                apt_id,
                patient[0] if patient else str(uuid.uuid4()),
                doctor[0],
                None,  # clinic_id
                None,  # department_id
                apt_data['date'],
                apt_data['time'],
                apt_data['status'],
                apt_data['reason'],
                apt_data['notes'],
                1,  # teleconsult_enabled = True
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            created_count += 1
            print(f"✓ Created appointment: {apt_data['reason']}")
            print(f"  Date: {apt_data['date']} at {apt_data['time']}")
            print(f"  ID: {apt_id}\n")
            
        except Exception as e:
            print(f"✗ Failed to create appointment: {str(e)}\n")
    
    conn.commit()
    conn.close()
    
    print("="*60)
    print(f"✅ Created {created_count} teleconsult appointments!")
    print("="*60)
    print("\nThese appointments will now appear on the Teleconsult page.")
    print("Both doctor and patient can see them and start video calls.")
    print("\nTo test:")
    print("1. Login as doctor@test.com")
    print("2. Go to Teleconsult page")
    print("3. Click 'Join Call' on any appointment")
    print("4. Video room will open with Jitsi Meet")

if __name__ == "__main__":
    create_teleconsult_appointments()
