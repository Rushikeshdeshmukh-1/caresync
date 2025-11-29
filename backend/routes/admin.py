"""
Admin Console Routes
Provides admin governance and system management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import uuid
from datetime import datetime
from sqlalchemy import text

from backend.middleware.rbac import require_role, ActorContext, Roles
from backend.decorators.audit import audit_action, audit_create
from backend.services.claim_composer import get_claim_composer
from models.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ==================== Request Models ====================

class ApproveProposalRequest(BaseModel):
    proposal_id: str
    notes: Optional[str] = None


class RejectProposalRequest(BaseModel):
    proposal_id: str
    reason: str


class GenerateClaimRequest(BaseModel):
    encounter_id: str
    claim_type: str = "dual"
    insurer_id: Optional[str] = None


class UpdateConfigRequest(BaseModel):
    key: str
    value: str


# ==================== Mapping Governance Routes ====================

@router.post("/mapping/proposals/{proposal_id}/approve")
@audit_action(resource="mapping_proposal", action="approve")
async def approve_mapping_proposal(
    request: Request,
    proposal_id: str,
    data: ApproveProposalRequest,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Approve mapping proposal (Admin only)
    
    NOTE: This only marks as approved. Manual migration still required.
    """
    session = SessionLocal()
    
    try:
        update_query = text("""
            UPDATE mapping_proposals
            SET status = 'approved',
                reviewed_by = :reviewed_by,
                reviewed_at = :reviewed_at,
                notes = :notes
            WHERE id = :proposal_id
        """)
        
        session.execute(update_query, {
            "reviewed_by": actor.actor_id,
            "reviewed_at": datetime.utcnow(),
            "notes": data.notes,
            "proposal_id": proposal_id
        })
        
        # Log admin action
        admin_action_query = text("""
            INSERT INTO admin_actions
            (admin_user_id, action_type, resource_type, resource_id, details, created_at)
            VALUES
            (:admin_user_id, :action_type, :resource_type, :resource_id, :details, :created_at)
        """)
        
        import json
        session.execute(admin_action_query, {
            "admin_user_id": actor.actor_id,
            "action_type": "approve_proposal",
            "resource_type": "mapping_proposal",
            "resource_id": proposal_id,
            "details": json.dumps({"notes": data.notes}),
            "created_at": datetime.utcnow()
        })
        
        session.commit()
        
        return {
            "status": "approved",
            "proposal_id": proposal_id,
            "message": "Proposal approved. Manual migration required to apply changes."
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error approving proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/mapping/proposals/{proposal_id}/reject")
@audit_action(resource="mapping_proposal", action="reject")
async def reject_mapping_proposal(
    request: Request,
    proposal_id: str,
    data: RejectProposalRequest,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Reject mapping proposal (Admin only)
    """
    session = SessionLocal()
    
    try:
        update_query = text("""
            UPDATE mapping_proposals
            SET status = 'rejected',
                reviewed_by = :reviewed_by,
                reviewed_at = :reviewed_at,
                notes = :notes
            WHERE id = :proposal_id
        """)
        
        session.execute(update_query, {
            "reviewed_by": actor.actor_id,
            "reviewed_at": datetime.utcnow(),
            "notes": data.reason,
            "proposal_id": proposal_id
        })
        
        session.commit()
        
        return {
            "status": "rejected",
            "proposal_id": proposal_id
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error rejecting proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ==================== Claims Management Routes ====================

@router.post("/claims/generate")
@audit_create(resource="claim_packet", extract_id=lambda r: r.get('claim_id'))
async def generate_claim(
    request: Request,
    data: GenerateClaimRequest,
    actor: ActorContext = Depends(require_role(Roles.ADMIN, Roles.DOCTOR))
):
    """
    Generate claim packet from encounter
    """
    try:
        claim_composer = get_claim_composer()
        
        result = claim_composer.generate_claim_packet(
            encounter_id=data.encounter_id,
            claim_type=data.claim_type,
            insurer_id=data.insurer_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating claim: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claims")
async def get_claims(
    status: Optional[str] = None,
    limit: int = 50,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Get claim packets (Admin only)
    """
    session = SessionLocal()
    
    try:
        if status:
            query = text("""
                SELECT id, encounter_id, patient_id, claim_type, status,
                       amount_claimed, amount_approved, created_at, submitted_at
                FROM claim_packets
                WHERE status = :status
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            results = session.execute(query, {"status": status, "limit": limit}).fetchall()
        else:
            query = text("""
                SELECT id, encounter_id, patient_id, claim_type, status,
                       amount_claimed, amount_approved, created_at, submitted_at
                FROM claim_packets
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            results = session.execute(query, {"limit": limit}).fetchall()
        
        claims = []
        for row in results:
            claims.append({
                "claim_id": row[0],
                "encounter_id": row[1],
                "patient_id": row[2],
                "claim_type": row[3],
                "status": row[4],
                "amount_claimed": row[5],
                "amount_approved": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "submitted_at": row[8].isoformat() if row[8] else None
            })
        
        return {
            "claims": claims,
            "count": len(claims)
        }
        
    finally:
        session.close()


# ==================== System Configuration Routes ====================

@router.get("/config")
async def get_system_config(actor: ActorContext = Depends(require_role(Roles.ADMIN))):
    """
    Get system configuration (Admin only)
    """
    session = SessionLocal()
    
    try:
        query = text("""
            SELECT key, value, value_type, description, updated_at
            FROM system_config
            ORDER BY key
        """)
        
        results = session.execute(query).fetchall()
        
        config = {}
        for row in results:
            key = row[0]
            value = row[1]
            value_type = row[2]
            
            # Parse value based on type
            if value_type == "boolean":
                config[key] = value.lower() == "true"
            elif value_type == "number":
                config[key] = float(value)
            elif value_type == "json":
                import json
                config[key] = json.loads(value)
            else:
                config[key] = value
        
        return config
        
    finally:
        session.close()


@router.put("/config")
@audit_action(resource="system_config", action="update")
async def update_system_config(
    request: Request,
    data: UpdateConfigRequest,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Update system configuration (Admin only)
    """
    session = SessionLocal()
    
    try:
        update_query = text("""
            UPDATE system_config
            SET value = :value,
                updated_by = :updated_by,
                updated_at = :updated_at
            WHERE key = :key
        """)
        
        session.execute(update_query, {
            "value": data.value,
            "updated_by": actor.actor_id,
            "updated_at": datetime.utcnow(),
            "key": data.key
        })
        
        session.commit()
        
        return {
            "status": "success",
            "key": data.key,
            "value": data.value
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ==================== Audit Log Routes ====================

@router.get("/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    actor: ActorContext = Depends(require_role(Roles.ADMIN))
):
    """
    Get audit logs (Admin only)
    """
    session = SessionLocal()
    
    try:
        if user_id and action:
            query = text("""
                SELECT id, user_id, actor_type, action, resource, resource_id,
                       status, timestamp
                FROM audit_logs
                WHERE user_id = :user_id AND action = :action
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            results = session.execute(query, {"user_id": user_id, "action": action, "limit": limit}).fetchall()
        elif user_id:
            query = text("""
                SELECT id, user_id, actor_type, action, resource, resource_id,
                       status, timestamp
                FROM audit_logs
                WHERE user_id = :user_id
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            results = session.execute(query, {"user_id": user_id, "limit": limit}).fetchall()
        elif action:
            query = text("""
                SELECT id, user_id, actor_type, action, resource, resource_id,
                       status, timestamp
                FROM audit_logs
                WHERE action = :action
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            results = session.execute(query, {"action": action, "limit": limit}).fetchall()
        else:
            query = text("""
                SELECT id, user_id, actor_type, action, resource, resource_id,
                       status, timestamp
                FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            results = session.execute(query, {"limit": limit}).fetchall()
        
        logs = []
        for row in results:
            logs.append({
                "id": row[0],
                "user_id": row[1],
                "actor_type": row[2],
                "action": row[3],
                "resource": row[4],
                "resource_id": row[5],
                "status": row[6],
                "timestamp": row[7].isoformat() if row[7] else None
            })
        
        return {
            "logs": logs,
            "count": len(logs)
        }
        
    finally:
        session.close()
