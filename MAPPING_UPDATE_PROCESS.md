# Manual Mapping Update Process

## Overview

The NAMASTE→ICD-11 mapping is **strictly read-only** and protected by multiple layers. Any updates to the mapping must follow this manual process to ensure data integrity and auditability.

## Governance Workflow

```
1. Clinician uses Co-Pilot → AI suggests mappings
                ↓
2. Clinician edits suggestion → Feedback stored in mapping_feedback
                ↓
3. Admin reviews feedback → Creates mapping_proposal
                ↓
4. Admin approves proposal → Status: "approved"
                ↓
5. Admin applies manual migration → Updates CSV files
                ↓
6. System detects changes → Mapping detector alerts
                ↓
7. Admin resets detector baseline → Confirms intentional update
                ↓
8. Version recorded → mapping_versions table
```

## Step-by-Step Process

### Step 1: Review Feedback Summary

**Admin Console:**
```bash
GET /api/mapping/feedback/summary?limit=50
```

**Response:**
```json
{
  "feedback_summary": [
    {
      "ayush_term": "Kasa",
      "suggested_icd11": "J20.9",
      "clinician_icd11": "R05",
      "correction_count": 15,
      "avg_confidence": 0.85
    }
  ]
}
```

**Action:** Identify terms with high correction counts (>10) and high confidence (>0.8).

### Step 2: Create Mapping Proposal

**Admin creates proposal:**
```bash
POST /api/mapping/propose-update
{
  "ayush_term": "Kasa",
  "current_icd11": "J20.9",
  "proposed_icd11": "R05",
  "reason": "15 clinicians consistently corrected to R05 (Cough) instead of J20.9 (Acute bronchitis)",
  "evidence": {
    "feedback_count": 15,
    "avg_confidence": 0.85,
    "clinician_ids": ["doc_001", "doc_002", ...]
  }
}
```

**Response:**
```json
{
  "proposal_id": "prop_123",
  "message": "Proposal created for admin review. Mapping will NOT be updated until manually approved and applied."
}
```

### Step 3: Review and Approve Proposal

**Review proposal:**
```bash
GET /api/mapping/proposals?status=pending
```

**Approve proposal:**
```bash
POST /api/admin/mapping/proposals/prop_123/approve
{
  "notes": "Reviewed with medical team. R05 is more appropriate for general cough symptom."
}
```

**IMPORTANT:** This only marks as approved. **No mapping changes occur yet.**

### Step 4: Manual CSV Update

**⚠️ CRITICAL: This is the ONLY way to update mappings**

1. **Backup current mapping:**
   ```bash
   cp data/namaste.csv data/namaste.csv.backup.$(date +%Y%m%d)
   ```

2. **Edit CSV file:**
   ```bash
   # Open data/namaste.csv
   # Find row: Kasa,NAMASTE_001,J20.9,Cough symptom
   # Update to: Kasa,NAMASTE_001,R05,Cough symptom
   ```

3. **Verify changes:**
   ```bash
   diff data/namaste.csv.backup.20250129 data/namaste.csv
   ```

### Step 5: Handle Detector Alert

**Expected behavior:** Mapping detector will alert on file modification.

```bash
# Run detector manually
python backend/monitoring/mapping_detector.py
```

**Output:**
```
MAPPING FILE MODIFIED: data/namaste.csv
  Baseline: 2025-01-28 10:00:00
  Current:  2025-01-29 15:30:00
MAPPING VIOLATION DETECTED: 1 violations found
```

**This is expected!** The alert confirms the protection system is working.

### Step 6: Reset Detector Baseline

**After verifying the update is intentional:**

```python
from backend.monitoring.mapping_detector import MappingDetector

detector = MappingDetector()
detector.reset_baselines()
print("✓ Baselines reset. New mapping version established.")
```

### Step 7: Record Mapping Version

**Create version record:**

```sql
INSERT INTO mapping_versions (version, changes, applied_by, applied_at, notes)
VALUES (
  'v1.1.0',
  '[{"ayush_term": "Kasa", "old_icd": "J20.9", "new_icd": "R05", "proposal_id": "prop_123"}]',
  'admin_user_id',
  CURRENT_TIMESTAMP,
  'Updated Kasa mapping based on clinician feedback'
);
```

### Step 8: Verify Update

**Test the new mapping:**

```bash
GET /api/mapping/lookup?ayush_term=Kasa
```

**Expected response:**
```json
{
  "found": true,
  "mapping": {
    "ayush_term": "Kasa",
    "icd_code": "R05",
    "source": "namaste_csv_exact_match"
  }
}
```

## Safety Checks

### Before Applying Update

- [ ] Proposal approved by admin
- [ ] Medical review completed
- [ ] Backup created
- [ ] Changes documented

### After Applying Update

- [ ] Detector baseline reset
- [ ] Version recorded in database
- [ ] Tests still passing (22/22)
- [ ] Mapping lookup returns new value

### Rollback Procedure

If update causes issues:

```bash
# 1. Restore backup
cp data/namaste.csv.backup.20250129 data/namaste.csv

# 2. Reset detector baseline
python -c "from backend.monitoring.mapping_detector import MappingDetector; MappingDetector().reset_baselines()"

# 3. Record rollback
INSERT INTO mapping_versions (version, changes, applied_by, notes)
VALUES ('v1.1.0-rollback', '[]', 'admin_user_id', 'Rolled back Kasa mapping update');
```

## Frequency Guidelines

**Recommended update cadence:**
- **Weekly:** Review feedback summary
- **Monthly:** Create proposals for high-confidence corrections
- **Quarterly:** Batch apply approved proposals
- **As needed:** Emergency corrections for critical errors

## Audit Trail

Every mapping update creates multiple audit records:

1. **mapping_feedback** - Clinician corrections
2. **mapping_proposals** - Admin proposals
3. **admin_actions** - Approval/rejection actions
4. **mapping_versions** - Applied changes
5. **orchestrator_audit** - Detector alerts

**Query full audit trail:**

```sql
SELECT 
  'feedback' as source, created_at, ayush_term, clinician_icd11
FROM mapping_feedback
WHERE ayush_term = 'Kasa'

UNION ALL

SELECT 
  'proposal' as source, created_at, ayush_term, proposed_icd11
FROM mapping_proposals
WHERE ayush_term = 'Kasa'

UNION ALL

SELECT
  'version' as source, applied_at, version, notes
FROM mapping_versions
WHERE changes LIKE '%Kasa%'

ORDER BY created_at DESC;
```

## Important Reminders

1. **Never modify mapping files directly in production** without following this process
2. **Always create backups** before making changes
3. **Document every change** in mapping_versions table
4. **Reset detector baseline** after intentional updates
5. **Run tests** after updates to ensure no regressions
6. **Communicate changes** to clinical team

## Emergency Contacts

If mapping protection system is triggered unexpectedly:

1. Check orchestrator status: `GET /api/health`
2. Review audit logs: `GET /api/admin/audit-logs?action=mapping_write_blocked`
3. If orchestrator paused: Resume via admin console
4. Investigate root cause before resuming

## Questions?

Refer to:
- Implementation Plan: `implementation_plan.md`
- Deployment Guide: `DEPLOYMENT.md`
- Walkthrough: `walkthrough.md`
