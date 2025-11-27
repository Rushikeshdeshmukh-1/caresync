"""
NAMASTE-ICD11 Terminology Microservice
FHIR R4-compliant service for integrating NAMASTE and ICD-11 codes
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fhir.resources.codesystem import CodeSystem
from fhir.resources.valueset import ValueSet
from fhir.resources.bundle import Bundle
from fhir.resources.condition import Condition
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# Request/Response Models
class SuggestRequest(BaseModel):
    term: str
    symptoms: Optional[str] = None
    language: Optional[str] = None
    k: int = 3


class SaveRecordRequest(BaseModel):
    patient_id: str
    clinician_id: str
    ayush_term: str
    icd_code: str
    notes: Optional[str] = None
    consent: bool = False
    confidence: Optional[float] = None
    provenance: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    record_id: str
    clinician_id: str
    action: str  # accepted, edited, rejected
    new_icd_code: Optional[str] = None
    comment: Optional[str] = None
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

from services.terminology_service import TerminologyService
from services.icd11_service import ICD11Service
from services.auth_service import AuthService
from services.audit_service import AuditService
from services.faiss_index import FaissIndex
from services.mapping_engine import MappingEngine
from services.orchestrator import Orchestrator
from models.database import init_db, get_db, ClinicalRecord, MappingFeedback, User, AyushTerm

# Import clinic management routes
from routes import (
    patients, appointments, encounters, prescriptions, billing, 
    dashboard, appointments_v2, prescriptions_v2, billing_v2, icd11, orchestrator, copilot
)

load_dotenv()

app = FastAPI(
    title="AYUSH Clinic Management System",
    description="Complete clinic/hospital management system with NAMASTE-ICD-11 dual coding integration",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # Added for current Vite dev server
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(encounters.router)
app.include_router(prescriptions.router)
app.include_router(billing.router)
app.include_router(dashboard.router)
app.include_router(appointments_v2.router)  # V2 routes
app.include_router(prescriptions_v2.router)  # V2 routes
app.include_router(billing_v2.router)  # V2 routes
app.include_router(icd11.router)
app.include_router(orchestrator.router)  # Orchestration endpoints
app.include_router(copilot.router)       # Co-Pilot Agent endpoints

# Security
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Services
terminology_service = TerminologyService()
icd11_service = ICD11Service()
auth_service = AuthService()
audit_service = AuditService()

# Agentic AI Services
faiss_index = FaissIndex()
mapping_engine = None  # Will be initialized after icd11_service
orchestrator = Orchestrator()

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize database
init_db()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_abha_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify ABHA OAuth 2.0 token"""
    token = credentials.credentials
    if not auth_service.verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired ABHA token")
    return token


async def get_optional_token(request: FastAPIRequest) -> str:
    """Get optional token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if auth_service.verify_token(token):
            return token
    return "demo-token"  # Default for demo


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global mapping_engine
    
    logger.info("Initializing NAMASTE-ICD11 Terminology Service with Agentic AI...")
    await terminology_service.initialize()
    await icd11_service.initialize()
    
    # Initialize mapping engine (CSV-based + API fallback)
    mapping_engine = MappingEngine(faiss_index, icd11_service)
    logger.info("Mapping engine initialized with CSV-based mapping (500 NAMASTE + 500 ICD-11 codes)")
    
    # Initialize FAISS index if available
    if faiss_index.is_loaded():
        logger.info("FAISS index loaded successfully")
    else:
        logger.warning("FAISS index not found. Run scripts/build_faiss_index.py to create it.")
    
    # Start orchestrator background task
    import asyncio
    asyncio.create_task(orchestrator.run())
    logger.info("Orchestrator agent started")
    
    logger.info("Service initialized successfully")


# ==================== FHIR Resources ====================

@app.get("/fhir/CodeSystem/namaste", response_model=CodeSystem)
async def get_namaste_codesystem():
    """Get NAMASTE CodeSystem resource"""
    return terminology_service.get_namaste_codesystem()


@app.get("/fhir/ValueSet/namaste-diagnosis", response_model=ValueSet)
async def get_namaste_valueset():
    """Get NAMASTE diagnosis ValueSet"""
    return terminology_service.get_namaste_valueset()


@app.get("/fhir/CodeSystem/icd11-tm2", response_model=CodeSystem)
async def get_icd11_tm2_codesystem():
    """Get ICD-11 TM2 CodeSystem"""
    return await icd11_service.get_tm2_codesystem()


@app.get("/fhir/CodeSystem/icd11-biomedicine", response_model=CodeSystem)
async def get_icd11_biomedicine_codesystem():
    """Get ICD-11 Biomedicine CodeSystem"""
    return await icd11_service.get_biomedicine_codesystem()


@app.get("/fhir/ConceptMap/namaste-to-icd11-tm2")
async def get_namaste_to_tm2_conceptmap():
    """Get ConceptMap for NAMASTE to ICD-11 TM2"""
    return terminology_service.get_namaste_to_tm2_conceptmap()


# ==================== API Endpoints ====================

@app.get("/api/search")
async def search_diagnosis(
    query: str,
    system: Optional[str] = None,
    limit: int = 20,
    request: FastAPIRequest = None,
    token: str = Depends(get_optional_token)
):
    """
    Auto-complete value-set lookup for diagnoses
    Supports NAMASTE, ICD-11 TM2, and ICD-11 Biomedicine
    """
    try:
        results = await terminology_service.search(query, system, limit)
        
        # Audit log
        await audit_service.log_access(
            user_token=token,
            resource="search",
            action="read",
            metadata={"query": query, "system": system}
        )
        
        return {"results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggest")
async def suggest_icd(
    request: SuggestRequest,
    token: str = Depends(get_optional_token)
):
    """
    Agentic AI suggestion endpoint
    Returns top-k ICD-11 suggestions for AYUSH term using rule-first → embedding → reranker pipeline
    """
    try:
        import time
        
        # Use mapping engine for suggestions (CSV-based + API)
        result = await mapping_engine.suggest(request.term, symptoms=request.symptoms, k=request.k)
        
        # Audit log
        await audit_service.log_access(
            user_token=token,
            resource="suggest",
            action="read",
            metadata={"term": request.term, "symptoms": request.symptoms, "k": request.k}
        )
        
        return {
            "status": "ok",
            "timestamp": time.time(),
            "data": result
        }
    except Exception as e:
        logger.error(f"Suggestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate")
async def translate_code(
    source_code: str,
    source_system: str,
    target_system: str,
    token: str = Depends(get_optional_token)
):
    """
    Translate codes between NAMASTE and ICD-11 TM2
    """
    try:
        result = await terminology_service.translate(
            source_code, source_system, target_system
        )
        
        # Audit log
        await audit_service.log_access(
            user_token=token,
            resource="translate",
            action="read",
            metadata={"source_code": source_code, "source_system": source_system, "target_system": target_system}
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/icd11/biomedicine")
async def lookup_icd11_biomedicine(
    code: Optional[str] = None,
    query: Optional[str] = None,
    token: str = Depends(get_optional_token)
):
    """
    Lookup ICD-11 Biomedicine codes
    """
    try:
        if code:
            result = await icd11_service.get_biomedicine_code(code)
        elif query:
            result = await icd11_service.search_biomedicine(query)
        else:
            raise HTTPException(status_code=400, detail="Either 'code' or 'query' parameter required")
        
        # Audit log
        await audit_service.log_access(
            user_token=token,
            resource="icd11_biomedicine",
            action="read",
            metadata={"code": code, "query": query}
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ICD-11 lookup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/save_record")
async def save_record(
    request: SaveRecordRequest,
    token: str = Depends(get_optional_token)
):
    """
    Save a dual-coded clinical record
    """
    try:
        from models.database import SessionLocal
        import uuid
        
        session = SessionLocal()
        
        # Get or create AYUSH term
        ayush_term_obj = session.query(AyushTerm).filter(AyushTerm.term == request.ayush_term).first()
        if not ayush_term_obj:
            ayush_term_obj = AyushTerm(
                id=str(uuid.uuid4()),
                term=request.ayush_term,
                source="user_input"
            )
            session.add(ayush_term_obj)
            session.commit()
        
        # Create clinical record
        record = ClinicalRecord(
            id=str(uuid.uuid4()),
            patient_id=request.patient_id,
            clinician_id=request.clinician_id,
            ayush_term_id=ayush_term_obj.id,
            icd_code=request.icd_code,
            notes=request.notes,
            consent=request.consent,
            confidence=request.confidence,
            provenance=request.provenance or {}
        )
        
        session.add(record)
        session.commit()
        record_id = record.id
        session.close()
        
        # Audit log
        await audit_service.log_access(
            user_token=token,
            resource="clinical_record",
            action="create",
            resource_id=record_id
        )
        
        return {
            "status": "success",
            "record_id": record_id
        }
    except Exception as e:
        logger.error(f"Save record error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    token: str = Depends(get_optional_token)
):
    """
    Submit feedback on a mapping for learning
    """
    try:
        from models.database import SessionLocal
        import uuid
        
        if request.action not in ['accepted', 'edited', 'rejected']:
            raise HTTPException(status_code=400, detail="Action must be 'accepted', 'edited', or 'rejected'")
        
        session = SessionLocal()
        
        # Create feedback entry
        feedback = MappingFeedback(
            id=str(uuid.uuid4()),
            record_id=request.record_id,
            clinician_id=request.clinician_id,
            action=request.action,
            new_icd_code=request.new_icd_code,
            comment=request.comment
        )
        
        session.add(feedback)
        session.commit()
        feedback_id = feedback.id
        session.close()
        
        # Audit log
        await audit_service.log_access(
            user_token=token,
            resource="mapping_feedback",
            action="create",
            resource_id=feedback_id
        )
        
        return {
            "status": "success",
            "feedback_id": feedback_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fhir/Bundle")
async def upload_fhir_bundle(
    bundle: Bundle,
    token: str = Depends(get_optional_token)
):
    """
    Upload FHIR Bundle with double-coding (NAMASTE + ICD-11)
    Validates ProblemList entries with both code systems
    """
    try:
        # Validate bundle and extract ProblemList entries
        validated_bundle = await terminology_service.validate_double_coding(bundle)
        
        # Store bundle
        bundle_id = await terminology_service.store_bundle(validated_bundle)
        
        # Audit log
        await audit_service.log_access(
            user_token=token,
            resource="bundle",
            action="create",
            resource_id=bundle_id
        )
        
        return {
            "status": "success",
            "bundle_id": bundle_id,
            "message": "Bundle uploaded and validated with double coding"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bundle upload error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Web Interface ====================

@app.get("/", response_class=HTMLResponse)
async def web_interface(request: FastAPIRequest):
    """Simple web interface for search and ProblemList creation"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AYUSH Clinic Management System",
        "version": "2.0.0",
        "features": [
            "Patient Management",
            "Appointment Scheduling",
            "Encounter Management",
            "NAMASTE-ICD-11 Dual Coding",
            "Prescription Management",
            "Billing & Invoicing",
            "Dashboard & Analytics"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
