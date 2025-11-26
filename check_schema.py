"""
Check bills_v2 table schema
"""

import sqlite3

def check_schema():
    conn = sqlite3.connect('terminology.db')
    cursor = conn.cursor()
    
    try:
        # Get table info
        cursor.execute("PRAGMA table_info(bills_v2)")
        columns = cursor.fetchall()
        
        print("Current bills_v2 schema:")
        print("-" * 60)
        for col in columns:
            print(f"  {col[1]:20} {col[2]:10} {'NOT NULL' if col[3] else ''} {f'DEFAULT {col[4]}' if col[4] else ''}")
        
        # Check which columns are missing
        column_names = [col[1] for col in columns]
        required_columns = ['prescription_id', 'paid_amount', 'payment_status', 'payment_method', 'payment_date', 'notes']
        
        missing = [col for col in required_columns if col not in column_names]
        
        if missing:
            print("\n❌ Missing columns:")
            for col in missing:
                print(f"  - {col}")
        else:
            print("\n✓ All required columns exist!")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()
