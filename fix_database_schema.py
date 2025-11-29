"""
Fix Database Schema - Add Missing Columns
"""

import sqlite3

def fix_schema():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    print("Checking and fixing database schema...\n")
    
    # Check users table
    users_cols = [col[1] for col in cursor.execute('PRAGMA table_info(users)').fetchall()]
    print(f"Users table has {len(users_cols)} columns")
    
    if 'password_hash' not in users_cols:
        print("  Adding password_hash column...")
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        print("  ✓ Added password_hash")
    else:
        print("  ✓ password_hash exists")
    
    if 'phone' not in users_cols:
        print("  Adding phone column...")
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        print("  ✓ Added phone")
    else:
        print("  ✓ phone exists")
    
    if 'is_active' not in users_cols:
        print("  Adding is_active column...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        print("  ✓ Added is_active")
    else:
        print("  ✓ is_active exists")
    
    if 'created_at' not in users_cols:
        print("  Adding created_at column...")
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP")
        print("  ✓ Added created_at")
    else:
        print("  ✓ created_at exists")
    
    # Check audit_logs table
    audit_cols = [col[1] for col in cursor.execute('PRAGMA table_info(audit_logs)').fetchall()]
    print(f"\nAudit_logs table has {len(audit_cols)} columns")
    
    if 'actor_type' not in audit_cols:
        print("  Adding actor_type column...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN actor_type TEXT")
        print("  ✓ Added actor_type")
    else:
        print("  ✓ actor_type exists")
    
    if 'payload' not in audit_cols:
        print("  Adding payload column...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN payload TEXT")
        print("  ✓ Added payload")
    else:
        print("  ✓ payload exists")
    
    if 'ip_address' not in audit_cols:
        print("  Adding ip_address column...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN ip_address TEXT")
        print("  ✓ Added ip_address")
    else:
        print("  ✓ ip_address exists")
    
    if 'user_agent' not in audit_cols:
        print("  Adding user_agent column...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN user_agent TEXT")
        print("  ✓ Added user_agent")
    else:
        print("  ✓ user_agent exists")
    
    if 'status' not in audit_cols:
        print("  Adding status column...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN status TEXT")
        print("  ✓ Added status")
    else:
        print("  ✓ status exists")
    
    if 'error_message' not in audit_cols:
        print("  Adding error_message column...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN error_message TEXT")
        print("  ✓ Added error_message")
    else:
        print("  ✓ error_message exists")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Database schema fixed!\n")

if __name__ == "__main__":
    fix_schema()
