# Agentic Orchestration Architecture

This document summarizes the agentic orchestration system implemented in the AYUSH Clinic Management System.

## Overview

The system implements an event-driven, agentic orchestration architecture with **read-only safeguards** preventing unauthorized modifications to mapping data.

## Key Components

### 1. Database Schema (4 New Tables)

- **`orchestrator_audit`**: Logs all orchestrator actions with evidence
- **`review_queue`**: Tasks requiring human review (low confidence, corrections)
- **`claim_packets`**: Generated insurance claims (preview/submitted states)
- **`model_metrics`**: Time-series model performance data

### 2. Safeguard System (`services/safeguards.py`)

**Critical Constraint**: Mapping data is **READ-ONLY**

Protected resources:
- `namaste.csv`
- `ayush_terms` table
- `mapping_candidates` table
- FAISS index files
- Model weights

Features:
- `safe_write()`: Blocks writes to mapping resources
- `audit_log()`: Records all actions
- `OrchestratorState`: Emergency pause mechanism
- Admin notifications for blocked writes

### 3. Event Bus (`services/event_bus.py`)

Redis Streams-based async messaging:

**Event Topics**:
- `encounter.created`
- `mapping.suggested`
- `encounter.dual_coded`
- `claim.previewed`
- `model.drift`

### 4. Orchestrator Service (`services/orchestrator_service.py`)

Main workflow coordinator:

**Workflow**:
1. Subscribe to `encounter.created` events
2. Extract AYUSH terms (NER/rules)
3. Call `MappingEngine.suggest()` (read-only)
4. Create `review_queue` tasks for low confidence (<0.7)
5. Publish `mapping.suggested` event
6. Generate claim previews (status='preview')

**Safeguards**:
- Never modifies mapping data
- All writes go through `safe_write()`
- Pauses on multiple blocked write attempts

### 5. API Endpoints (`routes/orchestrator.py`)

**Encounter Workflows**:
- `POST /api/orchestrator/encounters/{id}/accept_mapping` - Accept AI suggestions
- `POST /api/orchestrator/claims/preview` - Generate claim preview

**Review Queue**:
- `GET /api/orchestrator/review_queue` - Get pending reviews
- `POST /api/orchestrator/review_queue/{id}/resolve` - Resolve review task

**Management**:
- `GET /api/orchestrator/status` - Health check
- `POST /api/orchestrator/pause` - Emergency pause
- `POST /api/orchestrator/resume` - Resume operations
- `GET /api/orchestrator/audit` - View audit log

## Usage

### Starting the System

**3 Processes Required**:

```bash
# Terminal 1: API Server
uvicorn main:app --reload --port 8000

# Terminal 2: Orchestrator Service
python -m services.orchestrator_service

# Terminal 3: Frontend
cd frontend && npm run dev
```

### Testing Safeguards

```bash
# Run safeguard tests
pytest tests/test_safeguards.py -v

# Run orchestrator tests
pytest tests/test_orchestrator.py -v
```

### Creating an Encounter

```bash
curl -X POST http://localhost:8000/api/encounters \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-123",
    "clinician_id": "doc-456",
    "notes": "Patient has Amlapitta and heartburn"
  }'
```

**What Happens**:
1. Encounter saved to database
2. `encounter.created` event published
3. Orchestrator extracts AYUSH terms
4. Mapping suggestions generated (read-only)
5. Audit log created
6. Review task created if confidence < 0.7
7. `mapping.suggested` event published

### Accepting Mapping

```bash
curl -X POST http://localhost:8000/api/orchestrator/encounters/enc-123/accept_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "selected": [
      {"ayush": "Amlapitta", "icd11": "DA63", "confidence": 0.92}
    ],
    "actor": "doc-456"
  }'
```

### Emergency Pause

```bash
curl -X POST http://localhost:8000/api/orchestrator/pause
```

## Monitoring

### Audit Log

```bash
curl http://localhost:8000/api/orchestrator/audit?limit=50
```

### Review Queue

```bash
curl http://localhost:8000/api/orchestrator/review_queue?status=open
```

### Orchestrator Status

```bash
curl http://localhost:8000/api/orchestrator/status
```

## Security & Compliance

✅ **Read-only mapping enforcement**  
✅ **Comprehensive audit trails**  
✅ **Human-in-the-loop for all mapping changes**  
✅ **Emergency pause mechanism**  
✅ **Blocked write detection and alerts**

## Next Steps

1. **Install Redis** (for production event bus)
2. **Implement NER model** (replace rule-based term extraction)
3. **Add WebSocket notifications** (real-time clinician alerts)
4. **Create monitoring dashboard** (admin UI)
5. **Implement drift detection** (model performance monitoring)
6. **Add insurer templates** (claim generation)

## Files Created

- `models/database.py` - Added 4 orchestration tables
- `services/safeguards.py` - Read-only mapping protection
- `services/event_bus.py` - Redis Streams event bus
- `services/orchestrator_service.py` - Main orchestrator
- `routes/orchestrator.py` - API endpoints
- `tests/test_safeguards.py` - Safeguard tests
- `tests/test_orchestrator.py` - Workflow tests
