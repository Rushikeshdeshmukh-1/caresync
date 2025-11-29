"""
Enhanced Co-Pilot Routes with Mapping Feedback
Integrates read-only mapping client and feedback mechanisms
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime
from sqlalchemy import text

from backend.clients.mapping_client import get_mapping_client
from backend.middleware.rbac import require_auth, require_role, ActorContext, Roles
from backend.decorators.audit import audit_create, audit_action
from models.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mapping", tags=["mapping", "copilot"])


# ==================== Request/Response Models ====================

class MappingLookupRequest(BaseModel):
    ayush_term: str


class AcceptMappingRequest(BaseModel):
    encounter_id: str
    selected_mappings: List[Dict[str, Any]]  # List of {ayush_term, icd_code, clinician_edited, ...}


class MappingFeedbackRequest(BaseModel):
    encounter_id: str
    ayush_term: str
    suggested_icd11: str
    clinician_icd11: str
    feedback_type: str = "correction"  # correction, addition, removal
    notes: Optional[str] = None
    confidence_score: Optional[float] = None


class CounterfactualRequest(BaseModel):
    encounter_id: str
    ayush_term: str
    suggested_icd11: str


class ProposeMappingUpdateRequest(BaseModel):
    ayush_term: str
    current_icd11: Optional[str] = None
    proposed_icd11: str
    reason: str
    evidence: Optional[Dict[str, Any]] = None


# ==================== Mapping Lookup Routes ====================

@router.get("/lookup")
async def lookup_mapping(
    ayush_term: str,
    actor: ActorContext = Depends(require_auth)
):
    """
    Lookup AYUSH term in mapping (READ-ONLY)
    
    Uses read-only mapping client to ensure immutability
    """
    try:
        mapping_client = get_mapping_client()
        
        result = mapping_client.lookup(ayush_term)
        
        if not result:
            return {
                "found": False,
                "ayush_term": ayush_term,
                "message": "No mapping found"
            }
        
        return {
            "found": True,
            "mapping": result
        }
        
    except Exception as e:
        logger.error(f"Mapping lookup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_mappings(
    query: str,
    limit: int = 10,
    actor: ActorContext = Depends(require_auth)
):
    """
    Search NAMASTE terms by keyword (READ-ONLY)
    """
    try:
        mapping_client = get_mapping_client()
        
        results = mapping_client.search_namaste(query, limit=limit)
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Mapping search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_mapping_stats(actor: ActorContext = Depends(require_role(Roles.ADMIN, Roles.DOCTOR))):
    """
    Get mapping statistics (READ-ONLY)
    """
    try:
        mapping_client = get_mapping_client()
        
        stats = mapping_client.get_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Encounter Mapping Routes ====================

@router.post("/encounters/{encounter_id}/accept")
@audit_create(resource="encounter_diagnosis", extract_id=lambda r: r.get('encounter_id'))
async def accept_mapping(
    request: Request,
    encounter_id: str,
    data: AcceptMappingRequest,
    actor: ActorContext = Depends(require_role(Roles.DOCTOR))
):
    """
    Accept AI mapping suggestions for encounter (Doctor only)
    
    Writes ONLY to encounter_diagnoses table (additive)
    Does NOT modify mapping store
    """
    session = SessionLocal()
    
    try:
        import json
        
        # Verify encounter exists
        check_query = text("SELECT id FROM encounters WHERE id = :encounter_id")
        result = session.execute(check_query, {"encounter_id": encounter_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        # Process each selected mapping
        for mapping in data.selected_mappings:
            ayush_term = mapping.get('ayush_term')
            icd_code = mapping.get('icd_code')
            clinician_edited = mapping.get('clinician_edited', False)
            ai_suggestion_id = mapping.get('ai_suggestion_id')
            confidence = mapping.get('confidence')
            
            # Insert into encounter_diagnoses (additive only)
            insert_query = text("""
                INSERT INTO encounter_diagnoses
                (id, encounter_id, ayush_term_id, icd_code, diagnosis_type, 
                 accepted_from_ai, ai_suggestion_id, clinician_modified, 
                 confidence, provenance, created_at)
                VALUES
                (:id, :encounter_id, :ayush_term_id, :icd_code, :diagnosis_type,
                 :accepted_from_ai, :ai_suggestion_id, :clinician_modified,
                 :confidence, :provenance, :created_at)
            """)
            
            provenance = {
                "source": "copilot_suggestion",
                "clinician_id": actor.actor_id,
                "clinician_edited": clinician_edited,
                "accepted_at": datetime.utcnow().isoformat()
            }
            
            session.execute(insert_query, {
                "id": str(uuid.uuid4()),
                "encounter_id": encounter_id,
                "ayush_term_id": None,  # Could link to ayush_terms table if needed
                "icd_code": icd_code,
                "diagnosis_type": "primary",
                "accepted_from_ai": not clinician_edited,
                "ai_suggestion_id": ai_suggestion_id,
                "clinician_modified": clinician_edited,
                "confidence": confidence,
                "provenance": json.dumps(provenance),
                "created_at": datetime.utcnow()
            })
            
            # If clinician edited, create feedback entry
            if clinician_edited:
                suggested_icd = mapping.get('original_suggested_icd11', '')
                
                feedback_query = text("""
                    INSERT INTO mapping_feedback
                    (id, encounter_id, ayush_term, suggested_icd11, clinician_icd11,
                     clinician_id, feedback_type, confidence_score, notes, created_at)
                    VALUES
                    (:id, :encounter_id, :ayush_term, :suggested_icd11, :clinician_icd11,
                     :clinician_id, :feedback_type, :confidence_score, :notes, :created_at)
                """)
                
                session.execute(feedback_query, {
                    "id": str(uuid.uuid4()),
                    "encounter_id": encounter_id,
                    "ayush_term": ayush_term,
                    "suggested_icd11": suggested_icd,
                    "clinician_icd11": icd_code,
                    "clinician_id": actor.actor_id,
                    "feedback_type": "correction",
                    "confidence_score": confidence,
                    "notes": mapping.get('notes', ''),
                    "created_at": datetime.utcnow()
                })
        
        session.commit()
        
        logger.info(f"Accepted {len(data.selected_mappings)} mappings for encounter {encounter_id}")
        
        return {
            "status": "success",
            "encounter_id": encounter_id,
            "mappings_accepted": len(data.selected_mappings),
            "feedback_created": sum(1 for m in data.selected_mappings if m.get('clinician_edited'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error accepting mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/feedback")
@audit_create(resource="mapping_feedback", extract_id=lambda r: r.get('feedback_id'))
async def submit_mapping_feedback(
    request: Request,
    data: MappingFeedbackRequest,
    actor: ActorContext = Depends(require_role(Roles.DOCTOR))
):
    """
    Submit mapping correction feedback (Doctor only)
    
    Stores feedback for future mapping improvements
    Does NOT modify mapping store
    """
    session = SessionLocal()
    
    try:
        import json
        
        feedback_id = str(uuid.uuid4())
        
        insert_query = text("""
            INSERT INTO mapping_feedback
            (id, encounter_id, ayush_term, suggested_icd11, clinician_icd11,
             clinician_id, feedback_type, confidence_score, notes, created_at)
            VALUES
            (:id, :encounter_id, :ayush_term, :suggested_icd11, :clinician_icd11,
             :clinician_id, :feedback_type, :confidence_score, :notes, :created_at)
        """)
        
        session.execute(insert_query, {
            "id": feedback_id,
            "encounter_id": data.encounter_id,
            "ayush_term": data.ayush_term,
            "suggested_icd11": data.suggested_icd11,
            "clinician_icd11": data.clinician_icd11,
            "clinician_id": actor.actor_id,
            "feedback_type": data.feedback_type,
            "confidence_score": data.confidence_score,
            "notes": data.notes,
            "created_at": datetime.utcnow()
        })
        
        session.commit()
        
        logger.info(f"Mapping feedback submitted: {feedback_id}")
        
        return {
            "status": "success",
            "feedback_id": feedback_id
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ==================== Admin Mapping Governance Routes ====================

@router.post("/propose-update")
@audit_create(resource="mapping_proposal", extract_id=lambda r: r.get('proposal_id'))
async def propose_mapping_update(
    request: Request,
    data: ProposeMappingUpdateRequest,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Propose mapping update (Admin only)
    
    Creates proposal for review - does NOT modify mapping
    """
    session = SessionLocal()
    
    try:
        import json
        
        proposal_id = str(uuid.uuid4())
        
        insert_query = text("""
            INSERT INTO mapping_proposals
            (id, ayush_term, current_icd11, proposed_icd11, evidence, reason,
             status, proposed_by, created_at)
            VALUES
            (:id, :ayush_term, :current_icd11, :proposed_icd11, :evidence, :reason,
             :status, :proposed_by, :created_at)
        """)
        
        session.execute(insert_query, {
            "id": proposal_id,
            "ayush_term": data.ayush_term,
            "current_icd11": data.current_icd11,
            "proposed_icd11": data.proposed_icd11,
            "evidence": json.dumps(data.evidence or {}),
            "reason": data.reason,
            "status": "pending",
            "proposed_by": actor.actor_id,
            "created_at": datetime.utcnow()
        })
        
        session.commit()
        
        logger.info(f"Mapping proposal created: {proposal_id}")
        
        return {
            "status": "success",
            "proposal_id": proposal_id,
            "message": "Proposal created for admin review. Mapping will NOT be updated until manually approved and applied."
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/feedback/summary")
async def get_feedback_summary(
    limit: int = 50,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Get mapping feedback summary (Admin only)
    
    Shows most common corrections for mapping improvement
    """
    session = SessionLocal()
    
    try:
        query = text("""
            SELECT ayush_term, suggested_icd11, clinician_icd11, 
                   COUNT(*) as count,
                   AVG(confidence_score) as avg_confidence
            FROM mapping_feedback
            GROUP BY ayush_term, suggested_icd11, clinician_icd11
            ORDER BY count DESC
            LIMIT :limit
        """)
        
        results = session.execute(query, {"limit": limit}).fetchall()
        
        feedback_summary = []
        for row in results:
            feedback_summary.append({
                "ayush_term": row[0],
                "suggested_icd11": row[1],
                "clinician_icd11": row[2],
                "correction_count": row[3],
                "avg_confidence": float(row[4]) if row[4] else None
            })
        
        return {
            "feedback_summary": feedback_summary,
            "total_items": len(feedback_summary)
        }
        
    finally:
        session.close()


@router.get("/proposals")
async def get_mapping_proposals(
    status: Optional[str] = None,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Get mapping proposals (Admin only)
    """
    session = SessionLocal()
    
    try:
        if status:
            query = text("""
                SELECT id, ayush_term, current_icd11, proposed_icd11, reason, status, created_at
                FROM mapping_proposals
                WHERE status = :status
                ORDER BY created_at DESC
            """)
            results = session.execute(query, {"status": status}).fetchall()
        else:
            query = text("""
                SELECT id, ayush_term, current_icd11, proposed_icd11, reason, status, created_at
                FROM mapping_proposals
                ORDER BY created_at DESC
                LIMIT 100
            """)
            results = session.execute(query).fetchall()
        
        proposals = []
        for row in results:
            proposals.append({
                "proposal_id": row[0],
                "ayush_term": row[1],
                "current_icd11": row[2],
                "proposed_icd11": row[3],
                "reason": row[4],
                "status": row[5],
                "created_at": row[6].isoformat() if row[6] else None
            })
        
        return {
            "proposals": proposals,
            "count": len(proposals)
        }
        
    finally:
        session.close()
