# 🔧 DATABASE LOCKED - QUICK FIX

## Problem
```
ERROR: (sqlite3.OperationalError) database is locked
```

Patient login (and all logins) are failing because SQLite database is locked.

## Root Cause
Multiple processes accessing `terminology.db` simultaneously:
1. Backend trying to update `last_login`
2. Audit logging trying to write logs
3. Possibly other scripts running

## IMMEDIATE FIX

### Step 1: Stop All Processes Accessing Database
```bash
# Stop any running Python scripts that might be accessing the database
# Check for:
- create_sample_data.py
- test scripts
- other backend instances
```

### Step 2: Restart Backend ONLY
```bash
# Stop current backend (Ctrl+C)
# Then restart:
uvicorn main:app --reload --port 8000
```

### Step 3: Wait for Full Startup
Wait for this message:
```
INFO: Application startup complete.
```

### Step 4: Try Login Again
Now try logging in with patient@test.com / patient123

## PERMANENT FIX

### Option 1: Disable last_login Update (Quick)
Edit `backend/services/jwt_auth_service.py`:

Find the login method and comment out the last_login update:
```python
# Don't update last_login for now to avoid lock
# user.last_login = datetime.utcnow()
# session.commit()
```

### Option 2: Add WAL Mode (Better)
Add to database initialization:
```python
# Enable WAL mode for better concurrency
conn.execute('PRAGMA journal_mode=WAL')
```

### Option 3: Use PostgreSQL (Production)
For production, switch from SQLite to PostgreSQL which handles concurrent writes better.

## TEST IT

After restarting backend, test with:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"patient123"}'
```

Should return:
```json
{
  "user": {...},
  "access_token": "...",
  "token_type": "bearer"
}
```

## Why This Happened
SQLite locks the entire database file during writes. When login tries to:
1. Update last_login (WRITE)
2. Write audit log (WRITE)

At the same time, it causes a lock conflict.

## Quick Workaround
Just restart the backend and make sure no other scripts are running!
