# CareSync Platform API Reference

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.caresync.example.com`

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Get tokens via `/api/auth/login` or `/api/auth/register`.

## Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe",
  "role": "patient",  // patient, doctor
  "phone": "+1234567890"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

Response:
```json
{
  "user": {
    "id": "user_123",
    "name": "John Doe",
    "email": "user@example.com",
    "role": "patient"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Teleconsult

#### Create Video Room (Doctor Only)
```http
POST /api/teleconsult/create-room
Authorization: Bearer <token>
Content-Type: application/json

{
  "appointment_id": "appt_123",
  "host_name": "Dr. Smith"
}
```

#### Join Video Room
```http
POST /api/teleconsult/join-room
Authorization: Bearer <token>
Content-Type: application/json

{
  "appointment_id": "appt_123",
  "user_name": "John Doe"
}
```

### Payments

#### Create Payment Intent
```http
POST /api/payments/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "appointment_id": "appt_123",
  "patient_id": "patient_123",
  "amount": 500.00,
  "currency": "INR",
  "description": "Consultation fee"
}
```

#### Verify Payment
```http
POST /api/payments/verify
Authorization: Bearer <token>
Content-Type: application/json

{
  "payment_intent_id": "pi_123",
  "razorpay_payment_id": "pay_xyz",
  "razorpay_order_id": "order_abc",
  "razorpay_signature": "signature_hash"
}
```

### Mapping

#### Lookup AYUSH Term
```http
GET /api/mapping/lookup?ayush_term=Kasa
Authorization: Bearer <token>
```

Response:
```json
{
  "found": true,
  "mapping": {
    "ayush_term": "Kasa",
    "icd_code": "R05",
    "icd_title": "Cough",
    "source": "namaste_csv_exact_match"
  }
}
```

#### Search Mappings
```http
GET /api/mapping/search?query=cough&limit=10
Authorization: Bearer <token>
```

#### Accept AI Mapping Suggestions (Doctor Only)
```http
POST /api/mapping/encounters/enc_123/accept
Authorization: Bearer <token>
Content-Type: application/json

{
  "encounter_id": "enc_123",
  "selected_mappings": [
    {
      "ayush_term": "Kasa",
      "icd_code": "R05",
      "clinician_edited": false,
      "ai_suggestion_id": "sug_123",
      "confidence": 0.95
    }
  ]
}
```

### Admin

#### Approve Mapping Proposal (Admin Only)
```http
POST /api/admin/mapping/proposals/prop_123/approve
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "proposal_id": "prop_123",
  "notes": "Approved after medical review"
}
```

#### Generate Claim
```http
POST /api/admin/claims/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "encounter_id": "enc_123",
  "claim_type": "dual",  // ayush, icd11, dual
  "insurer_id": "ins_123"
}
```

#### Get System Configuration (Admin Only)
```http
GET /api/admin/config
Authorization: Bearer <admin_token>
```

#### View Audit Logs (Admin Only)
```http
GET /api/admin/audit-logs?user_id=user_123&limit=100
Authorization: Bearer <admin_token>
```

### Monitoring

#### Health Check
```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-29T00:00:00Z",
  "uptime_seconds": 86400,
  "components": {
    "database": {
      "status": "healthy"
    },
    "mapping_protection": {
      "status": "active",
      "protected": true
    }
  }
}
```

#### Prometheus Metrics
```http
GET /api/metrics
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied. Required role: admin"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- Default: 100 requests per minute per IP
- Authenticated: 1000 requests per minute per user
- Admin: Unlimited

## Pagination

List endpoints support pagination:

```http
GET /api/admin/claims?limit=50&offset=0
```

## Interactive Documentation

Visit `/docs` for interactive Swagger UI documentation.
