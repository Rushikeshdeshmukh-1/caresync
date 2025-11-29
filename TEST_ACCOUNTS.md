# Test User Accounts 🔐

## Quick Login Credentials

Use these pre-created accounts to test the CareSync platform:

### 👑 Admin Account
```
Email: admin@test.com
Password: admin123
```
**Access:** All features including Mapping Console and Audit Logs

### 👨‍⚕️ Doctor Account
```
Email: doctor@test.com
Password: doctor123
```
**Access:** Patients, Encounters, Prescriptions, Billing, Mapping, Orchestrator

### 🏥 Patient Account
```
Email: patient@test.com
Password: patient123
```
**Access:** Dashboard, Appointments, Prescriptions

---

## How to Use

1. **Open your browser** to http://localhost:5173
2. **Click Login** (should be the first page you see)
3. **Enter credentials** from above
4. **Explore features** based on your role

## What You'll See

### As Admin
- ✅ Full dashboard access
- ✅ Mapping Console (feedback & proposals)
- ✅ Audit Logs viewer
- ✅ All patient/doctor features

### As Doctor
- ✅ Patient management
- ✅ Encounter creation with AI Co-Pilot
- ✅ ICD-11 mapping suggestions
- ✅ Prescription writing
- ✅ Billing/invoicing

### As Patient
- ✅ View appointments
- ✅ View prescriptions
- ✅ Dashboard overview

## Platform Features to Test

1. **Authentication**
   - Login/Logout
   - Role-based menu items
   - User profile display

2. **Platform Status Banner**
   - Shows "Platform Transformed"
   - Lists features: JWT Auth, Teleconsult, Payments, Mapping Protection

3. **Admin Features** (admin@test.com only)
   - Navigate to "Mapping Console"
   - Navigate to "Audit Logs"
   - View system statistics

4. **Branding**
   - "CareSync" instead of "AyushCare"
   - "Platform Ready" indicator
   - Modern UI with gradient banner

## Troubleshooting

**If login fails:**
1. Make sure backend is running: `uvicorn main:app --reload --port 8000`
2. Check browser console for errors (F12)
3. Verify API is accessible: http://localhost:8000/docs

**If registration shows "email already registered":**
- Use the test accounts above instead
- Or use a completely unique email (e.g., yourname+test1@gmail.com)

**To create more test users:**
```bash
python create_test_users.py
```

---

**Backend API:** http://localhost:8000
**Frontend:** http://localhost:5173
**API Docs:** http://localhost:8000/docs
