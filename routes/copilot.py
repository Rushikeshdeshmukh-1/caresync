from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from models.database import get_db
from services.copilot_service import CoPilotService
from services.mapping_engine import MappingEngine
from services.icd11_service import ICD11Service

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

# Initialize services
icd11_service = ICD11Service()
mapping_engine = MappingEngine(icd11_service)
copilot_service = CoPilotService(mapping_engine)

class AnalyzeRequest(BaseModel):
    encounter_id: str
    notes: str
    patient_context: Dict[str, Any] = {}
    actor: str = "clinician"

class ChatRequest(BaseModel):
    encounter_id: str
    message: str
    context: Dict[str, Any] = {}

@router.post("/analyze")
async def analyze_encounter(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyze encounter notes and provide AI suggestions.
    """
    try:
        result = await copilot_service.analyze_encounter(
            db=db,
            encounter_id=request.encounter_id,
            notes=request.notes,
            patient_context=request.patient_context,
            actor=request.actor
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_copilot(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with the Co-Pilot agent about an encounter.
    """
    try:
        response = await copilot_service.chat(
            db=db,
            encounter_id=request.encounter_id,
            message=request.message,
            context=request.context
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
