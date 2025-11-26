-- Migration 005: Fix bill_items_v2 schema
-- Recreate table to replace line_total with amount and fix constraints

-- 1. Rename existing table
ALTER TABLE bill_items_v2 RENAME TO bill_items_v2_old;

-- 2. Create new table with correct schema
CREATE TABLE bill_items_v2 (
    id TEXT PRIMARY KEY,
    bill_id TEXT NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price REAL NOT NULL,
    amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills_v2(id) ON DELETE CASCADE
);

-- 3. Copy data (handle both old line_total and new amount columns)
-- Use coalesce to take amount if exists, else line_total, else 0
INSERT INTO bill_items_v2 (id, bill_id, description, quantity, unit_price, amount, created_at)
SELECT 
    id, 
    bill_id, 
    description, 
    quantity, 
    unit_price, 
    COALESCE(amount, line_total, 0) as amount, 
    created_at
FROM bill_items_v2_old;

-- 4. Create index
CREATE INDEX IF NOT EXISTS idx_bill_items_v2_bill ON bill_items_v2(bill_id);

-- 5. Drop old table
DROP TABLE bill_items_v2_old;
