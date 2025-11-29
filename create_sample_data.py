"""
Create Sample Data for Testing
Populates database with realistic test data
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
import random

def create_sample_data():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    print("Creating sample data for testing...\n")
    
    # Get existing users
    users = cursor.execute("SELECT id, name, role FROM users").fetchall()
    print(f"Found {len(users)} existing users")
    
    if len(users) < 2:
        print("Not enough users. Please run create_test_users.py first")
        return
    
    # Create sample patients if needed
    patient_count = cursor.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    if patient_count < 5:
        print(f"\nCreating sample patients (current: {patient_count})...")
        for i in range(5 - patient_count):
            patient_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO patients (id, user_id, name, date_of_birth, gender, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                users[0][0],  # Link to first user
                f"Sample Patient {i+1}",
                f"199{i}-0{i+1}-15",
                random.choice(['Male', 'Female', 'Other']),
                f"+91 98765432{i}0",
                datetime.utcnow()
            ))
        print(f"✓ Created {5 - patient_count} sample patients")
    
    # Create sample appointments
    apt_count = cursor.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    if apt_count < 5:
        print(f"\nCreating sample appointments (current: {apt_count})...")
        patients = cursor.execute("SELECT id, name FROM patients LIMIT 5").fetchall()
        
        for i in range(5 - apt_count):
            apt_date = datetime.utcnow() + timedelta(days=i+1)
            cursor.execute("""
                INSERT INTO appointments (id, patient_id, doctor_id, date, time, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                patients[i % len(patients)][0],
                users[1][0] if len(users) > 1 else users[0][0],
                apt_date.strftime('%Y-%m-%d'),
                f"{9 + i}:00 AM",
                random.choice(['scheduled', 'completed', 'cancelled']),
                f"Follow-up consultation {i+1}",
                datetime.utcnow()
            ))
        print(f"✓ Created {5 - apt_count} sample appointments")
    
    # Create sample encounters
    enc_count = cursor.execute("SELECT COUNT(*) FROM encounters").fetchone()[0]
    if enc_count < 3:
        print(f"\nCreating sample encounters (current: {enc_count})...")
        patients = cursor.execute("SELECT id FROM patients LIMIT 3").fetchall()
        
        diagnoses = [
            "Common Cold with Fever",
            "Hypertension - Stage 1",
            "Type 2 Diabetes Mellitus"
        ]
        
        for i in range(3 - enc_count):
            cursor.execute("""
                INSERT INTO encounters (id, patient_id, doctor_id, date, diagnosis, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                patients[i % len(patients)][0],
                users[1][0] if len(users) > 1 else users[0][0],
                datetime.utcnow().strftime('%Y-%m-%d'),
                diagnoses[i],
                f"Patient presented with symptoms. Treatment prescribed.",
                datetime.utcnow()
            ))
        print(f"✓ Created {3 - enc_count} sample encounters")
    
    # Create sample prescriptions
    presc_count = cursor.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
    if presc_count < 3:
        print(f"\nCreating sample prescriptions (current: {presc_count})...")
        patients = cursor.execute("SELECT id FROM patients LIMIT 3").fetchall()
        
        medications = [
            "Paracetamol 500mg - Take 1 tablet every 6 hours",
            "Amlodipine 5mg - Take 1 tablet daily",
            "Metformin 500mg - Take 1 tablet twice daily"
        ]
        
        for i in range(3 - presc_count):
            cursor.execute("""
                INSERT INTO prescriptions (id, patient_id, doctor_id, medication, dosage, frequency, duration, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                patients[i % len(patients)][0],
                users[1][0] if len(users) > 1 else users[0][0],
                medications[i].split(' - ')[0],
                "As prescribed",
                medications[i].split(' - ')[1],
                "7 days",
                "Take with food",
                datetime.utcnow()
            ))
        print(f"✓ Created {3 - presc_count} sample prescriptions")
    
    # Create sample billing records
    bill_count = cursor.execute("SELECT COUNT(*) FROM billing").fetchone()[0]
    if bill_count < 3:
        print(f"\nCreating sample billing records (current: {bill_count})...")
        patients = cursor.execute("SELECT id FROM patients LIMIT 3").fetchall()
        
        for i in range(3 - bill_count):
            amount = random.choice([500, 750, 1000, 1500])
            cursor.execute("""
                INSERT INTO billing (id, patient_id, amount, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                patients[i % len(patients)][0],
                amount,
                f"Consultation and treatment - Visit {i+1}",
                random.choice(['paid', 'pending', 'overdue']),
                datetime.utcnow()
            ))
        print(f"✓ Created {3 - bill_count} sample billing records")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ Sample data creation complete!")
    print("="*60)
    print("\nYour platform now has:")
    print("- Sample patients")
    print("- Sample appointments")
    print("- Sample encounters")
    print("- Sample prescriptions")
    print("- Sample billing records")
    print("\nAll features should now display data!")

if __name__ == "__main__":
    create_sample_data()
