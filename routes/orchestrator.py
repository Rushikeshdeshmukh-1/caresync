"""
Orchestration API Routes
Endpoints for encounter workflows, review queue, and orchestrator management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.event_bus import event_bus, EventTopics
from services.safeguards import audit_log, orchestrator_state
from models.database import SessionLocal, Encounter, ReviewQueue, ClaimPacket, OrchestratorAudit

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


# ==================== Request/Response Models ====================

class AcceptMappingRequest(BaseModel):
    """Request to accept AI mapping suggestion"""
    selected: List[Dict[str, Any]]
    actor: str  # clinician ID


class ClaimPreviewRequest(BaseModel):
    """Request to generate claim preview"""
    encounter_id: str
    insurer: str


class ResolveReviewRequest(BaseModel):
    """Request to resolve review task"""
    resolution: Dict[str, Any]
    resolved_by: str


# ==================== Encounter Workflow Endpoints ====================

@router.post("/encounters/{encounter_id}/accept_mapping")
async def accept_mapping(encounter_id: str, request: AcceptMappingRequest):
    """
    Accept AI mapping suggestions for an encounter
    Creates dual-coded encounter and publishes event
    """
    try:
        session = SessionLocal()
        
        # Get encounter
        encounter = session.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        # Create audit log
        audit_log(
            action="mapping_accepted",
            actor=request.actor,
            status="success",
            encounter_id=encounter_id,
            payload_summary={
                "num_mappings": len(request.selected),
                "mappings": request.selected
            }
        )
        
        # Publish encounter.dual_coded event
        event_bus.publish(EventTopics.ENCOUNTER_DUAL_CODED, {
            "encounter_id": encounter_id,
            "dual_coded": request.selected,
            "timestamp": datetime.utcnow().isoformat(),
            "actor": request.actor
        })
        
        session.close()
        
        return {
            "status": "success",
            "encounter_id": encounter_id,
            "message": "Mapping accepted and dual-coding complete"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Claims Endpoints ====================

@router.post("/claims/preview")
async def create_claim_preview(request: ClaimPreviewRequest):
    """
    Generate insurance claim preview
    Does NOT submit - requires explicit approval
    """
    try:
        session = SessionLocal()
        
        # Get encounter
        encounter = session.query(Encounter).filter(Encounter.id == request.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        # Generate claim JSON (simplified for now)
        claim_json = {
            "encounter_id": request.encounter_id,
            "patient_id": encounter.patient_id,
            "insurer": request.insurer,
            "generated_at": datetime.utcnow().isoformat(),
            # TODO: Add actual claim fields based on insurer template
        }
        
        # Save claim packet with status='preview'
        claim_packet = ClaimPacket(
            encounter_id=request.encounter_id,
            patient_id=encounter.patient_id,
            insurer=request.insurer,
            claim_json=claim_json,
            status='preview'
        )
        
        session.add(claim_packet)
        session.commit()
        claim_id = claim_packet.id
        
        # Publish event
        event_bus.publish(EventTopics.CLAIM_PREVIEWED, {
            "claim_id": claim_id,
            "encounter_id": request.encounter_id,
            "insurer": request.insurer
        })
        
        # Audit log
        audit_log(
            action="claim_preview_generated",
            actor="orchestrator_agent",
            status="success",
            encounter_id=request.encounter_id,
            payload_summary={"claim_id": claim_id, "insurer": request.insurer}
        )
        
        session.close()
        
        return {
            "status": "success",
            "claim_id": claim_id,
            "claim_json": claim_json
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Review Queue Endpoints ====================

@router.get("/review_queue")
async def get_review_queue(
    status: Optional[str] = "open",
    limit: int = 50
):
    """Get pending review tasks"""
    try:
        session = SessionLocal()
        
        query = session.query(ReviewQueue)
        if status:
            query = query.filter(ReviewQueue.status == status)
        
        tasks = query.order_by(ReviewQueue.created_at.desc()).limit(limit).all()
        
        result = [{
            "id": task.id,
            "encounter_id": task.encounter_id,
            "reason": task.reason,
            "priority": task.priority,
            "payload": task.payload,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None
        } for task in tasks]
        
        session.close()
        
        return {
            "status": "success",
            "tasks": result,
            "count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review_queue/{task_id}/resolve")
async def resolve_review_task(task_id: int, request: ResolveReviewRequest):
    """Resolve a review task"""
    try:
        session = SessionLocal()
        
        task = session.query(ReviewQueue).filter(ReviewQueue.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Review task not found")
        
        task.status = 'resolved'
        task.resolution = request.resolution
        task.resolved_at = datetime.utcnow()
        task.assigned_to = request.resolved_by
        
        session.commit()
        session.close()
        
        # Audit log
        audit_log(
            action="review_task_resolved",
            actor=request.resolved_by,
            status="success",
            payload_summary={"task_id": task_id, "resolution": request.resolution}
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Review task resolved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Orchestrator Management Endpoints ====================

@router.get("/status")
async def get_orchestrator_status():
    """Get orchestrator status"""
    return {
        "status": "active" if orchestrator_state.is_active() else "paused",
        "mode": orchestrator_state._mode,
        "blocked_write_count": orchestrator_state._blocked_write_count,
        "last_reset": orchestrator_state._last_reset.isoformat()
    }


@router.post("/pause")
async def pause_orchestrator():
    """Emergency pause orchestrator"""
    orchestrator_state.pause()
    
    # Publish event
    event_bus.publish(EventTopics.ORCHESTRATOR_PAUSED, {
        "timestamp": datetime.utcnow().isoformat(),
        "reason": "manual_pause"
    })
    
    return {
        "status": "success",
        "message": "Orchestrator paused"
    }


@router.post("/resume")
async def resume_orchestrator():
    """Resume orchestrator"""
    orchestrator_state.resume()
    
    return {
        "status": "success",
        "message": "Orchestrator resumed"
    }


@router.get("/audit")
async def get_audit_log(
    limit: int = 100,
    status: Optional[str] = None,
    action: Optional[str] = None
):
    """Get orchestrator audit log"""
    try:
        session = SessionLocal()
        
        query = session.query(OrchestratorAudit)
        if status:
            query = query.filter(OrchestratorAudit.status == status)
        if action:
            query = query.filter(OrchestratorAudit.action == action)
        
        logs = query.order_by(OrchestratorAudit.timestamp.desc()).limit(limit).all()
        
        result = [{
            "id": log.id,
            "action": log.action,
            "actor": log.actor,
            "status": log.status,
            "encounter_id": log.encounter_id,
            "resource_target": log.resource_target,
            "attempted_write": log.attempted_write,
            "error_message": log.error_message,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        } for log in logs]
        
        session.close()
        
        return {
            "status": "success",
            "logs": result,
            "count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
