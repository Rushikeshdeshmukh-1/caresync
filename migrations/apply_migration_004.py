"""
Apply migration 004 to fix bills_v2 schema
"""

import sqlite3

def apply_migration():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    try:
        # Read migration file
        with open('migrations/004_fix_bills_v2_schema.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        cursor.executescript(migration_sql)
        conn.commit()
        print("✓ Migration 004 applied successfully!")
        print("  - Added prescription_id column")
        print("  - Added paid_amount column")
        print("  - Added payment_status column")
        print("  - Added payment_method column")
        print("  - Added payment_date column")
        print("  - Added notes column")
        print("  - Added amount column to bill_items_v2")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error applying migration: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()
