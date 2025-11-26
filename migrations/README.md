# Database Migration Guide

## Overview

This directory contains migration scripts to upgrade the Appointments, Prescriptions, and Billing modules to V2 schema.

## Migration Files

- `001_create_v2_tables.sql` - Creates new V2 tables
- `002_migrate_data.py` - Migrates data from old to new tables
- `003_rollback.sql` - Rolls back V2 tables
- `004_fix_bills_v2_schema.sql` - Fixes bills_v2 schema
- `005_fix_bill_items_schema.sql` - Fixes bill_items_v2 schema

## Pre-Migration Checklist

- [ ] Backup database: `cp terminology.db terminology.db.backup`
- [ ] Stop application servers
- [ ] Review migration plan
- [ ] Run dry-run migration

## Migration Steps

### 1. Backup Database

```bash
cp terminology.db terminology.db.backup
```

### 2. Create V2 Tables

```bash
sqlite3 terminology.db < migrations/001_create_v2_tables.sql
```

### 3. Run Dry-Run Migration

```bash
python migrations/002_migrate_data.py --dry-run
```

Review the output to ensure no errors.

### 4. Run Actual Migration

```bash
python migrations/002_migrate_data.py
```

### 5. Verify Migration

The migration script will automatically verify counts. You can also manually check:

```sql
-- Check appointments
SELECT COUNT(*) FROM appointments;
SELECT COUNT(*) FROM appointments_v2;

-- Check prescriptions
SELECT COUNT(*) FROM prescriptions;
SELECT COUNT(*) FROM prescriptions_v2;

-- Check billing
SELECT COUNT(*) FROM invoices;
SELECT COUNT(*) FROM bills_v2;
```

## Rollback Procedure

If you need to rollback:

### 1. Stop Application

### 2. Run Rollback Script

```bash
sqlite3 terminology.db < migrations/003_rollback.sql
```

### 3. Restore Backup (if needed)

```bash
cp terminology.db.backup terminology.db
```

## Verification Queries

After migration, run these queries to verify data integrity:

```sql
-- Verify appointments have valid references
SELECT COUNT(*) FROM appointments_v2 a
LEFT JOIN patients p ON a.patient_id = p.id
WHERE p.id IS NULL;
-- Should return 0

-- Verify prescriptions have items
SELECT p.id, COUNT(pi.id) as item_count
FROM prescriptions_v2 p
LEFT JOIN prescription_items_v2 pi ON p.id = pi.prescription_id
GROUP BY p.id
HAVING item_count = 0;
-- Should return empty or expected prescriptions without items

-- Verify bill totals match items
SELECT b.id, b.total_amount, SUM(bi.line_total) as items_total
FROM bills_v2 b
LEFT JOIN bill_items_v2 bi ON b.id = bi.bill_id
GROUP BY b.id
HAVING ABS(b.total_amount - COALESCE(items_total, 0)) > 0.01;
-- Should return empty or acceptable discrepancies
```

## Troubleshooting

### Migration Fails with Foreign Key Error

Ensure patients and staff tables have the referenced IDs. Check:

```sql
SELECT DISTINCT patient_id FROM appointments 
WHERE patient_id NOT IN (SELECT id FROM patients);
```

### Duplicate ID Errors

Old and new tables use the same IDs. This is intentional for data continuity.

### Performance Issues

For large datasets, consider:
- Running migration during low-traffic hours
- Adding `PRAGMA journal_mode=WAL;` before migration
- Increasing SQLite cache size

## Post-Migration

After successful migration:

1. Deploy new V2 API routes
2. Update frontend to use V2 endpoints
3. Monitor for 24-48 hours
4. If stable, consider deprecating old tables (keep for 30 days)

## Support

For issues, check:
- Migration script output for specific errors
- Database logs
- Application logs after deploying V2 routes
