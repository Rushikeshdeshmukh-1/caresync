"""
Test Database Schema
"""
import sqlite3

def test_database():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    # Get all tables
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    
    print(f"✓ Database has {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check critical tables
    critical_tables = [
        'users', 'patients', 'clinicians', 'organizations',
        'appointments', 'encounters', 'prescriptions',
        'payment_intents', 'teleconsult_sessions',
        'claim_packets', 'mapping_proposals', 'audit_logs'
    ]
    
    existing_tables = [t[0] for t in tables]
    
    print("\n✓ Critical tables check:")
    for table in critical_tables:
        status = "✓" if table in existing_tables else "✗"
        print(f"  {status} {table}")
    
    conn.close()
    return True

if __name__ == "__main__":
    test_database()
