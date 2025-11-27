import sqlite3
import os

# Database path
DB_PATH = "terminology.db"

def fix_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Starting schema migration...")

        # 1. Disable foreign keys
        cursor.execute("PRAGMA foreign_keys=OFF")

        # 2. Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # 3. Create new table with correct schema (staff_id nullable)
        # Note: We are copying the schema from models/database.py but making staff_id nullable
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encounters_new (
                id VARCHAR PRIMARY KEY,
                patient_id VARCHAR NOT NULL,
                staff_id VARCHAR,
                appointment_id VARCHAR,
                clinic_id VARCHAR,
                encounter_type VARCHAR DEFAULT 'outpatient',
                chief_complaint TEXT,
                history_of_present_illness TEXT,
                examination TEXT,
                assessment TEXT,
                plan TEXT,
                status VARCHAR DEFAULT 'in_progress',
                visit_date DATETIME,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(patient_id) REFERENCES patients(id),
                FOREIGN KEY(staff_id) REFERENCES staff(id),
                FOREIGN KEY(appointment_id) REFERENCES appointments(id),
                FOREIGN KEY(clinic_id) REFERENCES clinics(id)
            )
        """)

        # 4. Copy data from old table to new table
        # We need to list columns explicitly to ensure correct mapping
        cursor.execute("""
            INSERT INTO encounters_new (
                id, patient_id, staff_id, appointment_id, clinic_id, 
                encounter_type, chief_complaint, history_of_present_illness, 
                examination, assessment, plan, status, visit_date, 
                created_at, updated_at
            )
            SELECT 
                id, patient_id, staff_id, appointment_id, clinic_id, 
                encounter_type, chief_complaint, history_of_present_illness, 
                examination, assessment, plan, status, visit_date, 
                created_at, updated_at
            FROM encounters
        """)
        print("Data copied successfully.")

        # 5. Drop old table
        cursor.execute("DROP TABLE encounters")

        # 6. Rename new table to old table name
        cursor.execute("ALTER TABLE encounters_new RENAME TO encounters")

        # 7. Commit transaction
        conn.commit()
        print("Schema migration completed successfully.")

        # 8. Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
