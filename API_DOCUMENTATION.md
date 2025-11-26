# API Documentation

The AYUSH Clinic Management System provides a comprehensive REST API built with FastAPI.

## 📚 Interactive Documentation

When the backend server is running, you can access the auto-generated interactive documentation at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) - Test endpoints directly from your browser.
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) - Alternative documentation view.

## 🚀 Key Endpoints

### Core Modules (V2)
- **Appointments**: `/api/v2/appointments` - Manage patient appointments.
- **Prescriptions**: `/api/v2/prescriptions` - Create and manage prescriptions.
- **Billing**: `/api/v2/billing` - Invoice generation and payment tracking.

### Clinical & AI Services
- **Search Diagnosis**: `/api/search` - Search for diagnoses across NAMASTE and ICD-11 systems.
- **AI Suggestions**: `/api/suggest` - Get AI-powered ICD-11 suggestions for AYUSH terms.
- **Translation**: `/api/translate` - Translate codes between systems.
- **ICD-11 Lookup**: `/api/icd11/biomedicine` - Look up standard biomedical codes.

### FHIR Resources
- **CodeSystem**: `/fhir/CodeSystem/namaste`
- **ValueSet**: `/fhir/ValueSet/namaste-diagnosis`
- **Bundle**: `/fhir/Bundle` - Upload dual-coded clinical data.

### System
- **Health Check**: `/health` - Verify system status and version.

## 🔐 Authentication

The API uses OAuth 2.0 with Bearer tokens.
- **Header**: `Authorization: Bearer <token>`
- **Demo Mode**: The system currently accepts `demo-token` or any non-empty string for testing purposes.

## 💻 Frontend Integration

The React frontend communicates with the backend using standard `fetch` API calls.

### Configuration
The base URL is typically defined as a constant in component files or environment variables:
```javascript
const API_BASE = 'http://localhost:8000';
```

### Usage Pattern
Components typically fetch data in `useEffect` hooks and handle loading/error states:

```javascript
// Example from PrescriptionsV2.jsx
const fetchPrescriptions = async () => {
    try {
        setLoading(true);
        const response = await fetch(`${API_BASE}/api/v2/prescriptions`);
        const data = await response.json();
        setPrescriptions(data.prescriptions || []);
    } catch (error) {
        console.error('Error fetching prescriptions:', error);
    } finally {
        setLoading(false);
    }
};
```

### Proxy Configuration
For development, `vite.config.js` is configured to proxy requests:
```javascript
server: {
    proxy: {
        '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true,
        }
    }
}
```

## 🛠️ Running the Server

To start the backend server and access the API:

```bash
python run.py
```

The server will start at `http://0.0.0.0:8000`.
