# AYUSH Clinic Management System

## Overview
A comprehensive clinic management system designed for AYUSH practitioners, featuring intelligent appointment scheduling, prescription management, billing, and AI-powered clinical assistance.

## 🚀 Key Features

### 1. Appointments Module (V2)
- **Smart Scheduling**: Interactive calendar with drag-and-drop support.
- **Patient Management**: Quick patient search and registration.
- **Status Tracking**: Track appointments (Scheduled, Confirmed, Completed, Cancelled).
- **Auto-Calculation**: Automatic end-time calculation based on slot duration.

### 2. Prescriptions Module (V2)
- **Digital Prescriptions**: Create detailed prescriptions with multiple medicines.
- **Medicine Database**: Manage medicine names, forms, doses, and frequencies.
- **History**: View patient prescription history.
- **Printing**: Generate PDF prescriptions (Coming Soon).

### 3. Billing Module (V2)
- **Invoice Generation**: Create professional invoices for consultations and treatments.
- **Payment Tracking**: Record partial or full payments (Cash, Card, UPI).
- **Financial Status**: Track paid, unpaid, and overdue bills.
- **Integration**: Linked directly to patients and appointments.

### 4. AI Clinical Assistant (Phase 1)
- **Symptom Analysis**: AI-powered analysis of patient symptoms.
- **ICD-11 Mapping**: Automatic mapping of symptoms to standard ICD-11 codes.
- **Ayush Terminology**: Integration with traditional AYUSH terms.

### 5. Dashboard
- **Real-time Stats**: Daily appointments, revenue, and patient counts.
- **Quick Actions**: Fast access to common tasks.

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python), SQLite
- **Frontend**: React, Vite, TailwindCSS
- **AI/ML**: Google Gemini Pro Integration
- **Database**: SQLite with V2 schema optimization
- **Authentication**: OAuth 2.0 (In Progress)

## 🏁 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (if needed)
python migrations/apply_migration_005.py

# Start server
python run.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📂 Project Structure
```
/services           # Backend business logic (V2 modules)
  /appointments_v2  # Appointment management
  /prescriptions_v2 # Prescription handling
  /billing_v2       # Billing and payments
/routes             # API endpoints
/models             # Database models
/frontend           # React application
  /src/features     # Feature-based components
  /src/pages        # Main page views
```

## 🔄 Recent Updates (V2 Rebuild)
- **Complete Backend Overhaul**: Migrated to modular V2 services.
- **Database Optimization**: New schema for better performance and data integrity.
- **UI Refresh**: Modern, responsive interface using TailwindCSS.
- **Bug Fixes**: Resolved CORS issues, dropdown bugs, and schema mismatches.
