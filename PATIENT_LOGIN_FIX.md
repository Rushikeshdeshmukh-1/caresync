# 🔍 Patient Login Issue - Diagnosis & Fix

## Issue Reported
Patient login is not working

## Investigation Results

### 1. Backend Timeout Issue
- Backend API is timing out (>10 seconds)
- Caused by heavy ML model loading on startup
- Affects all API endpoints including login

### 2. Patient User Accounts
Need to verify if patient accounts exist with proper password hashes.

## Quick Fixes

### Fix 1: Check if Patient Users Exist
```python
# Run this to check patient users
import sqlite3
conn = sqlite3.connect('terminology.db')
cursor = conn.cursor()

users = cursor.execute("""
    SELECT id, email, name, role 
    FROM users 
    WHERE role='patient'
""").fetchall()

print("Patient users in database:")
for user in users:
    print(f"  - {user[2]} ({user[1]})")

conn.close()
```

### Fix 2: Create Patient Test Account (if missing)
```python
# create_patient_account.py
import sqlite3
import bcrypt
import uuid
from datetime import datetime

conn = sqlite3.connect('terminology.db')
cursor = conn.cursor()

# Hash password
password = "patient123"
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Create patient user
patient_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO users 
    (id, name, email, password_hash, role, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    patient_id,
    "Test Patient",
    "patient@test.com",
    password_hash,
    "patient",
    1,
    datetime.utcnow()
))

conn.commit()
conn.close()

print("✓ Patient account created!")
print("  Email: patient@test.com")
print("  Password: patient123")
```

### Fix 3: Backend Performance Issue
The backend is slow because of ML model loading. Two options:

**Option A: Lazy Loading (Quick Fix)**
- Load models only when needed, not on startup
- Faster startup time

**Option B: Optimize Startup (Better)**
- Keep models in memory but optimize loading
- Add timeout handling in frontend

## Test Patient Login

### Via Frontend:
1. Go to http://localhost:5173
2. Enter:
   - Email: patient@test.com
   - Password: patient123
3. Click Login

### Via API:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"patient@test.com","password":"patient123"}'
```

## Expected Response
```json
{
  "user": {
    "id": "...",
    "name": "Test Patient",
    "email": "patient@test.com",
    "role": "patient"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

## Common Issues & Solutions

### Issue: "Invalid email or password"
**Cause:** Password hash doesn't match
**Fix:** Recreate user account with correct password hash

### Issue: "User not found"
**Cause:** No patient user in database
**Fix:** Run create_patient_account.py script

### Issue: Backend timeout
**Cause:** ML models loading on startup
**Fix:** Wait 30-60 seconds for backend to fully start, or optimize model loading

### Issue: "Missing or invalid authorization header"
**Cause:** Token not being sent from frontend
**Fix:** Check useAuth hook is working correctly

## Verification Steps

1. **Check Backend is Running:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy",...}`

2. **Check Patient User Exists:**
   ```sql
   SELECT * FROM users WHERE email='patient@test.com';
   ```

3. **Test Login API:**
   Use curl command above

4. **Check Frontend:**
   - Open browser console (F12)
   - Try to login
   - Check for errors in console

## Recommended Action

Run the create_patient_account.py script to ensure a patient user exists with the correct password hash.

Then test login again!
