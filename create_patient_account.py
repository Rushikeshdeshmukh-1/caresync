"""
Create Patient Test Account
Ensures a patient user exists for testing
"""

import sqlite3
import bcrypt
import uuid
from datetime import datetime

def create_patient_account():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    # Check if patient already exists
    existing = cursor.execute("""
        SELECT id, email FROM users WHERE email='patient@test.com'
    """).fetchone()
    
    if existing:
        print("✓ Patient account already exists!")
        print(f"  Email: patient@test.com")
        print(f"  ID: {existing[0]}")
        print("\nYou can login with:")
        print("  Email: patient@test.com")
        print("  Password: patient123")
        conn.close()
        return
    
    # Hash password
    password = "patient123"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Create patient user
    patient_id = str(uuid.uuid4())
    
    try:
        cursor.execute("""
            INSERT INTO users 
            (id, name, email, password_hash, role, is_active, email_verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            "Test Patient",
            "patient@test.com",
            password_hash,
            "patient",
            1,
            0,
            datetime.utcnow()
        ))
        
        conn.commit()
        
        print("✓ Patient account created successfully!")
        print(f"  ID: {patient_id}")
        print(f"  Name: Test Patient")
        print(f"  Email: patient@test.com")
        print(f"  Password: patient123")
        print(f"  Role: patient")
        print("\nYou can now login with these credentials!")
        
    except Exception as e:
        print(f"✗ Error creating patient account: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_patient_account()
