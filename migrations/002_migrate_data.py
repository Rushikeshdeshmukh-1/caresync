"""
Data Migration Script: Old Tables -> V2 Tables
Migrates existing appointments, prescriptions, and billing data to new schema
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

def connect_db(db_path: str = "terminology.db") -> sqlite3.Connection:
    """Connect to the database"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_appointments(conn: sqlite3.Connection, dry_run: bool = False) -> Dict[str, int]:
    """Migrate appointments from old to new schema"""
    cursor = conn.cursor()
    
    # Fetch old appointments
    old_appointments = cursor.execute("""
        SELECT id, patient_id, staff_id, appointment_date, appointment_time,
               status, reason, notes, created_at, updated_at
        FROM appointments
    """).fetchall()
    
    migrated = 0
    errors = []
    
    for appt in old_appointments:
        try:
            # Parse date and time
            appt_date = appt['appointment_date']
            appt_time = appt['appointment_time'] or '00:00'
            
            # Combine date and time
            if isinstance(appt_date, str):
                start_time = f"{appt_date} {appt_time}"
            else:
                start_time = appt_date
            
            # Calculate end time (default 30 minutes)
            try:
                start_dt = datetime.fromisoformat(str(start_time).replace('Z', ''))
                end_dt = start_dt + timedelta(minutes=30)
                end_time = end_dt.isoformat()
            except:
                end_time = start_time  # Fallback
            
            if not dry_run:
                cursor.execute("""
                    INSERT INTO appointments_v2 
                    (id, patient_id, doctor_id, start_time, end_time, 
                     status, reason, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    appt['id'],
                    appt['patient_id'],
                    appt['staff_id'],
                    start_time,
                    end_time,
                    appt['status'] or 'scheduled',
                    appt['reason'],
                    appt['notes'],
                    appt['created_at'],
                    appt['updated_at']
                ))
            
            migrated += 1
        except Exception as e:
            errors.append(f"Appointment {appt['id']}: {str(e)}")
    
    if not dry_run:
        conn.commit()
    
    return {
        'total': len(old_appointments),
        'migrated': migrated,
        'errors': errors
    }

def migrate_prescriptions(conn: sqlite3.Connection, dry_run: bool = False) -> Dict[str, int]:
    """Migrate prescriptions from old to new schema"""
    cursor = conn.cursor()
    
    # Fetch old prescriptions
    old_prescriptions = cursor.execute("""
        SELECT id, encounter_id, patient_id, staff_id, 
               prescription_date, notes, status, created_at
        FROM prescriptions
    """).fetchall()
    
    migrated = 0
    items_migrated = 0
    errors = []
    
    for pres in old_prescriptions:
        try:
            # Map encounter to appointment (if exists)
            appointment_id = None
            if pres['encounter_id']:
                enc = cursor.execute("""
                    SELECT appointment_id FROM encounters WHERE id = ?
                """, (pres['encounter_id'],)).fetchone()
                if enc and enc['appointment_id']:
                    # Check if appointment exists in v2
                    appt_v2 = cursor.execute("""
                        SELECT id FROM appointments_v2 WHERE id = ?
                    """, (enc['appointment_id'],)).fetchone()
                    if appt_v2:
                        appointment_id = enc['appointment_id']
            
            if not dry_run:
                cursor.execute("""
                    INSERT INTO prescriptions_v2 
                    (id, patient_id, doctor_id, appointment_id, 
                     issued_at, diagnosis, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pres['id'],
                    pres['patient_id'],
                    pres['staff_id'],
                    appointment_id,
                    pres['prescription_date'] or pres['created_at'],
                    '',  # No diagnosis in old schema
                    pres['notes'],
                    pres['created_at']
                ))
            
            # Migrate prescription items
            old_items = cursor.execute("""
                SELECT id, medicine_id, medicine_name, dosage, 
                       frequency, duration, instructions, created_at
                FROM prescription_items
                WHERE prescription_id = ?
            """, (pres['id'],)).fetchall()
            
            for item in old_items:
                if not dry_run:
                    cursor.execute("""
                        INSERT INTO prescription_items_v2 
                        (id, prescription_id, medicine_name, form, dose, 
                         frequency, duration, instructions, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['id'],
                        pres['id'],
                        item['medicine_name'],
                        '',  # No form in old schema
                        item['dosage'],
                        item['frequency'],
                        item['duration'],
                        item['instructions'],
                        item['created_at']
                    ))
                items_migrated += 1
            
            migrated += 1
        except Exception as e:
            errors.append(f"Prescription {pres['id']}: {str(e)}")
    
    if not dry_run:
        conn.commit()
    
    return {
        'total': len(old_prescriptions),
        'migrated': migrated,
        'items_migrated': items_migrated,
        'errors': errors
    }

def migrate_billing(conn: sqlite3.Connection, dry_run: bool = False) -> Dict[str, int]:
    """Migrate billing from old to new schema"""
    cursor = conn.cursor()
    
    # Fetch old invoices
    old_invoices = cursor.execute("""
        SELECT id, encounter_id, patient_id, clinic_id, invoice_number,
               invoice_date, subtotal, tax, discount, total, status,
               payment_method, notes, created_at
        FROM invoices
    """).fetchall()
    
    migrated = 0
    items_migrated = 0
    payments_migrated = 0
    errors = []
    
    for inv in old_invoices:
        try:
            # Map encounter to appointment
            appointment_id = None
            if inv['encounter_id']:
                enc = cursor.execute("""
                    SELECT appointment_id FROM encounters WHERE id = ?
                """, (inv['encounter_id'],)).fetchone()
                if enc and enc['appointment_id']:
                    appt_v2 = cursor.execute("""
                        SELECT id FROM appointments_v2 WHERE id = ?
                    """, (enc['appointment_id'],)).fetchone()
                    if appt_v2:
                        appointment_id = enc['appointment_id']
            
            if not dry_run:
                cursor.execute("""
                    INSERT INTO bills_v2 
                    (id, patient_id, appointment_id, status, 
                     total_amount, tax_amount, discount_amount, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inv['id'],
                    inv['patient_id'],
                    appointment_id,
                    inv['status'] or 'unpaid',
                    inv['total'] or 0,
                    inv['tax'] or 0,
                    inv['discount'] or 0,
                    inv['created_at'],
                    inv['created_at']
                ))
            
            # Migrate invoice items
            old_items = cursor.execute("""
                SELECT id, item_type, item_name, quantity, 
                       unit_price, total, created_at
                FROM invoice_items
                WHERE invoice_id = ?
            """, (inv['id'],)).fetchall()
            
            for item in old_items:
                if not dry_run:
                    cursor.execute("""
                        INSERT INTO bill_items_v2 
                        (id, bill_id, description, quantity, 
                         unit_price, tax_percent, line_total, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['id'],
                        inv['id'],
                        f"{item['item_type']}: {item['item_name']}",
                        item['quantity'] or 1,
                        item['unit_price'] or 0,
                        0,  # No tax percent in old schema
                        item['total'] or 0,
                        item['created_at']
                    ))
                items_migrated += 1
            
            # Migrate payments
            old_payments = cursor.execute("""
                SELECT id, amount, payment_method, payment_date,
                       transaction_id, notes, created_at
                FROM payments
                WHERE invoice_id = ?
            """, (inv['id'],)).fetchall()
            
            for pmt in old_payments:
                if not dry_run:
                    cursor.execute("""
                        INSERT INTO payments_v2 
                        (id, bill_id, amount, method, txn_ref, 
                         payment_date, notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pmt['id'],
                        inv['id'],
                        pmt['amount'],
                        pmt['payment_method'],
                        pmt['transaction_id'],
                        pmt['payment_date'],
                        pmt['notes'],
                        pmt['created_at']
                    ))
                payments_migrated += 1
            
            migrated += 1
        except Exception as e:
            errors.append(f"Invoice {inv['id']}: {str(e)}")
    
    if not dry_run:
        conn.commit()
    
    return {
        'total': len(old_invoices),
        'migrated': migrated,
        'items_migrated': items_migrated,
        'payments_migrated': payments_migrated,
        'errors': errors
    }

def verify_migration(conn: sqlite3.Connection) -> Dict[str, Dict]:
    """Verify migration by comparing counts"""
    cursor = conn.cursor()
    
    verification = {}
    
    # Appointments
    old_count = cursor.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    new_count = cursor.execute("SELECT COUNT(*) FROM appointments_v2").fetchone()[0]
    verification['appointments'] = {'old': old_count, 'new': new_count, 'match': old_count == new_count}
    
    # Prescriptions
    old_count = cursor.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
    new_count = cursor.execute("SELECT COUNT(*) FROM prescriptions_v2").fetchone()[0]
    verification['prescriptions'] = {'old': old_count, 'new': new_count, 'match': old_count == new_count}
    
    # Prescription Items
    old_count = cursor.execute("SELECT COUNT(*) FROM prescription_items").fetchone()[0]
    new_count = cursor.execute("SELECT COUNT(*) FROM prescription_items_v2").fetchone()[0]
    verification['prescription_items'] = {'old': old_count, 'new': new_count, 'match': old_count == new_count}
    
    # Invoices/Bills
    old_count = cursor.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    new_count = cursor.execute("SELECT COUNT(*) FROM bills_v2").fetchone()[0]
    verification['bills'] = {'old': old_count, 'new': new_count, 'match': old_count == new_count}
    
    return verification

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate data to v2 tables')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--db', default='terminology.db', help='Database path')
    args = parser.parse_args()
    
    print(f"{'DRY RUN - ' if args.dry_run else ''}Starting migration...")
    print(f"Database: {args.db}\n")
    
    conn = connect_db(args.db)
    
    try:
        # Migrate appointments
        print("Migrating appointments...")
        appt_result = migrate_appointments(conn, args.dry_run)
        print(f"  Total: {appt_result['total']}, Migrated: {appt_result['migrated']}")
        if appt_result['errors']:
            print(f"  Errors: {len(appt_result['errors'])}")
            for err in appt_result['errors'][:5]:
                print(f"    - {err}")
        
        # Migrate prescriptions
        print("\nMigrating prescriptions...")
        pres_result = migrate_prescriptions(conn, args.dry_run)
        print(f"  Total: {pres_result['total']}, Migrated: {pres_result['migrated']}")
        print(f"  Items migrated: {pres_result['items_migrated']}")
        if pres_result['errors']:
            print(f"  Errors: {len(pres_result['errors'])}")
            for err in pres_result['errors'][:5]:
                print(f"    - {err}")
        
        # Migrate billing
        print("\nMigrating billing...")
        bill_result = migrate_billing(conn, args.dry_run)
        print(f"  Total: {bill_result['total']}, Migrated: {bill_result['migrated']}")
        print(f"  Items migrated: {bill_result['items_migrated']}")
        print(f"  Payments migrated: {bill_result['payments_migrated']}")
        if bill_result['errors']:
            print(f"  Errors: {len(bill_result['errors'])}")
            for err in bill_result['errors'][:5]:
                print(f"    - {err}")
        
        # Verify if not dry run
        if not args.dry_run:
            print("\nVerifying migration...")
            verification = verify_migration(conn)
            for table, counts in verification.items():
                status = "✓" if counts['match'] else "✗"
                print(f"  {status} {table}: {counts['old']} -> {counts['new']}")
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"\nError during migration: {str(e)}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
