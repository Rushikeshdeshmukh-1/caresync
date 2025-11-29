"""
Apply Phase 2 Migration: Teleconsult & Payments
"""

import sqlite3
from pathlib import Path

def apply_migration():
    """Apply Phase 2 migration"""
    db_path = Path("terminology.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    migration_path = Path("migrations/007_teleconsult_payments.sql")
    
    if not migration_path.exists():
        print(f"Error: Migration file not found at {migration_path}")
        return False
    
    try:
        # Read migration SQL
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Execute migration
        print("Applying Phase 2 migration (Teleconsult & Payments)...")
        cursor.executescript(migration_sql)
        
        conn.commit()
        conn.close()
        
        print("✓ Phase 2 migration applied successfully")
        return True
        
    except Exception as e:
        print(f"Error applying migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    apply_migration()
