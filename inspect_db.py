"""
Inspect database tables
"""

import sqlite3

def inspect_db():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables:")
        for t in tables:
            print(f"  - {t[0]}")
            
        # Check bill_items_v2 schema
        print("\nSchema of bill_items_v2:")
        try:
            cursor.execute("PRAGMA table_info(bill_items_v2)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        except:
            print("  (Table not found)")

        # Check bill_items_v2_old schema
        print("\nSchema of bill_items_v2_old:")
        try:
            cursor.execute("PRAGMA table_info(bill_items_v2_old)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        except:
            print("  (Table not found)")
            
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_db()
