"""
Cleanup migration 005 artifacts
"""

import sqlite3

def cleanup():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    try:
        # Drop old table if exists
        cursor.execute("DROP TABLE IF EXISTS bill_items_v2_old")
        print("✓ Dropped bill_items_v2_old")
        
        # Ensure index exists on new table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bill_items_v2_bill_new ON bill_items_v2(bill_id)")
        print("✓ Verified index on bill_items_v2")
        
        conn.commit()
        print("Cleanup complete!")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error during cleanup: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup()
