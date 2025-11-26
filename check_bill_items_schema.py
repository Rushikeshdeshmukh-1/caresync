"""
Check bill_items_v2 table schema
"""

import sqlite3

def check_schema():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    try:
        # Get table info
        cursor.execute("PRAGMA table_info(bill_items_v2)")
        columns = cursor.fetchall()
        
        print("Current bill_items_v2 schema:")
        print("-" * 60)
        for col in columns:
            print(f"  {col[1]:20} {col[2]:10} {'NOT NULL' if col[3] else ''} {f'DEFAULT {col[4]}' if col[4] else ''}")
        
        # Check for amount column
        column_names = [col[1] for col in columns]
        
        if 'amount' not in column_names:
            print("\n❌ Missing 'amount' column - need to add it!")
            print("   (Currently has 'line_total' instead)")
        else:
            print("\n✓ 'amount' column exists!")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()
