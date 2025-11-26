"""
Apply SQL migration to database
"""
import sqlite3
import sys

def apply_migration(db_path='terminology.db', sql_file='migrations/001_create_v2_tables.sql'):
    """Apply SQL migration from file"""
    try:
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute SQL statements
        cursor.executescript(sql)
        conn.commit()
        conn.close()
        
        print(f"✓ Migration applied successfully from {sql_file}")
        return True
        
    except Exception as e:
        print(f"✗ Error applying migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
