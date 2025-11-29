import sqlite3
import os

DB_PATH = "terminology.db"

def enable_wal_mode():
    print(f"Enabling WAL mode for {DB_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check current journal mode
        cursor.execute("PRAGMA journal_mode;")
        current_mode = cursor.fetchone()[0]
        print(f"Current journal mode: {current_mode}")
        
        if current_mode.upper() != 'WAL':
            # Enable WAL mode
            cursor.execute("PRAGMA journal_mode=WAL;")
            new_mode = cursor.fetchone()[0]
            print(f"New journal mode: {new_mode}")
            
            if new_mode.upper() == 'WAL':
                print("WAL mode enabled successfully!")
            else:
                print("Failed to enable WAL mode.")
        else:
            print("WAL mode is already enabled.")
            
        conn.close()
        
    except Exception as e:
        print(f"Error enabling WAL mode: {e}")

if __name__ == "__main__":
    enable_wal_mode()
