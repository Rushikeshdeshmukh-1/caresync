"""
Create Test User Accounts
Creates dummy accounts for testing the platform
"""

import sqlite3
import bcrypt
import uuid
from datetime import datetime

def create_test_users():
    """Create test user accounts"""
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    # Test accounts to create
    test_users = [
        {
            'email': 'admin@test.com',
            'password': 'admin123',
            'name': 'Admin User',
            'role': 'admin',
            'phone': '+91 9876543210'
        },
        {
            'email': 'doctor@test.com',
            'password': 'doctor123',
            'name': 'Dr. Test Doctor',
            'role': 'doctor',
            'phone': '+91 9876543211'
        },
        {
            'email': 'patient@test.com',
            'password': 'patient123',
            'name': 'Test Patient',
            'role': 'patient',
            'phone': '+91 9876543212'
        }
    ]
    
    print("Creating test user accounts...\n")
    
    for user_data in test_users:
        # Check if user already exists
        existing = cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (user_data['email'],)
        ).fetchone()
        
        if existing:
            print(f"⚠️  User {user_data['email']} already exists, skipping...")
            continue
        
        # Hash password
        password_hash = bcrypt.hashpw(
            user_data['password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Create user
        user_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO users (id, name, email, role, password_hash, phone, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_data['name'],
            user_data['email'],
            user_data['role'],
            password_hash,
            user_data['phone'],
            True,
            datetime.utcnow()
        ))
        
        # If doctor, create clinician record
        if user_data['role'] == 'doctor':
            clinician_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO clinicians (id, user_id, license_number, specialization, is_verified)
                VALUES (?, ?, ?, ?, ?)
            """, (
                clinician_id,
                user_id,
                'TEST-' + user_id[:8],
                'General Practice',
                True
            ))
        
        # If patient, create patient record
        if user_data['role'] == 'patient':
            patient_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO patients (id, user_id, name, date_of_birth, gender, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                user_id,
                user_data['name'],
                '1990-01-01',
                'Other',
                user_data['phone'],
                datetime.utcnow()
            ))
        
        print(f"✓ Created {user_data['role']}: {user_data['email']}")
        print(f"  Password: {user_data['password']}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("TEST ACCOUNTS CREATED")
    print("="*60)
    print("\n📧 Admin Account:")
    print("   Email: admin@test.com")
    print("   Password: admin123")
    print("\n👨‍⚕️ Doctor Account:")
    print("   Email: doctor@test.com")
    print("   Password: doctor123")
    print("\n🏥 Patient Account:")
    print("   Email: patient@test.com")
    print("   Password: patient123")
    print("\n" + "="*60)
    print("Use these credentials to login at http://localhost:5173")
    print("="*60 + "\n")

if __name__ == "__main__":
    create_test_users()
