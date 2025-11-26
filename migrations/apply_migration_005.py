"""
Apply migration 005 to fix bill_items_v2 schema
"""

import sqlite3

def apply_migration():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    try:
        # Read migration file
        with open('migrations/005_fix_bill_items_schema.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        cursor.executescript(migration_sql)
        conn.commit()
        print("✓ Migration 005 applied successfully!")
        print("  - Recreated bill_items_v2 table")
        print("  - Fixed 'amount' column")
        print("  - Removed 'line_total' constraint")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error applying migration: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()
