"""
Apply Phase 4 Migration: Claims & Admin Console
"""

import sqlite3
from pathlib import Path

def apply_migration():
    """Apply Phase 4 migration"""
    db_path = Path("terminology.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    migration_path = Path("migrations/009_claims_admin.sql")
    
    if not migration_path.exists():
        print(f"Error: Migration file not found at {migration_path}")
        return False
    
    try:
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Applying Phase 4 migration (Claims & Admin Console)...")
        cursor.executescript(migration_sql)
        
        conn.commit()
        conn.close()
        
        print("✓ Phase 4 migration applied successfully")
        return True
        
    except Exception as e:
        print(f"Error applying migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    apply_migration()
