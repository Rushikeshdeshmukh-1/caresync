"""
Safeguard System for Orchestrator
Prevents unauthorized writes to mapping data resources
"""

import logging
import json
import yaml
import os
from datetime import datetime
from typing import Any, Dict, Set
from pathlib import Path
from models.database import SessionLocal, OrchestratorAudit

logger = logging.getLogger(__name__)

# Load protected mapping resources from config file
def _load_mapping_resources() -> Set[str]:
    """Load protected mapping resources from YAML config"""
    config_path = Path("config/mapping_resources.yml")
    
    if not config_path.exists():
        logger.warning(f"Mapping resources config not found at {config_path}, using defaults")
        # Fallback to hardcoded defaults
        return {
            "namaste.csv",
            "data/namaste.csv",
            "namaste_mappings_table",
            "ayush_terms",
            "mapping_candidates",
            "mapping_index_faiss",
            "data/faiss_index.bin",
            "mapping_model_weights",
            "data/reranker.joblib"
        }
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            resources = set(config.get('mapping_resources', []))
            logger.info(f"Loaded {len(resources)} protected mapping resources from config")
            return resources
    except Exception as e:
        logger.error(f"Error loading mapping resources config: {str(e)}")
        return set()

# Immutable set of protected mapping resources
MAPPING_DATA_RESOURCES: Set[str] = _load_mapping_resources()


def is_mapping_resource(resource: str) -> bool:
    """
    Check if a resource is a protected mapping resource
    
    Args:
        resource: Resource identifier (file path, table name, etc.)
        
    Returns:
        True if resource is protected, False otherwise
    """
    # Normalize path separators
    normalized = resource.replace("\\", "/")
    
    # Check exact matches
    if normalized in MAPPING_DATA_RESOURCES:
        return True
    
    # Check if any protected resource is in the path
    for protected in MAPPING_DATA_RESOURCES:
        if protected in normalized:
            return True
    
    return False


def audit_log(
    action: str,
    actor: str,
    status: str,
    resource_target: str = None,
    payload_summary: Dict[str, Any] = None,
    model_version: str = None,
    evidence: Dict[str, Any] = None,
    attempted_write: bool = False,
    error_message: str = None,
    encounter_id: str = None
) -> int:
    """
    Create an audit log entry
    
    Args:
        action: Action being performed
        actor: Who is performing the action
        status: success, blocked, failed
        resource_target: Resource being accessed
        payload_summary: Summary of the payload
        model_version: Model version if applicable
        evidence: Evidence/context for the action
        attempted_write: Whether this was a write attempt
        error_message: Error message if failed
        encounter_id: Related encounter ID
        
    Returns:
        Audit log ID
    """
    try:
        session = SessionLocal()
        
        audit_entry = OrchestratorAudit(
            action=action,
            actor=actor,
            status=status,
            resource_target=resource_target,
            payload_summary=payload_summary,
            model_version=model_version,
            evidence=evidence,
            attempted_write=attempted_write,
            error_message=error_message,
            encounter_id=encounter_id,
            timestamp=datetime.utcnow()
        )
        
        session.add(audit_entry)
        session.commit()
        audit_id = audit_entry.id
        session.close()
        
        logger.info(f"Audit log created: {action} - {status} (ID: {audit_id})")
        return audit_id
        
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        # Don't fail the operation if audit logging fails
        return -1


def notify_admin(title: str, details: Dict[str, Any]):
    """
    Send notification to admin (placeholder for email/Slack integration)
    
    Args:
        title: Notification title
        details: Notification details
    """
    logger.critical(f"ADMIN ALERT: {title}")
    logger.critical(f"Details: {json.dumps(details, indent=2)}")
    
    # TODO: Implement actual notification (email, Slack, etc.)
    # For now, just log critically


def safe_write(
    resource: str,
    payload: Any,
    actor: str = "orchestrator_agent",
    encounter_id: str = None
) -> bool:
    """
    Safely write to a resource with mapping protection
    
    Args:
        resource: Resource identifier
        payload: Data to write
        actor: Who is performing the write
        encounter_id: Related encounter ID
        
    Returns:
        True if write is allowed and successful, False otherwise
        
    Raises:
        PermissionError: If attempting to write to protected mapping resource
    """
    # Check if this is a protected mapping resource
    if is_mapping_resource(resource):
        # Create audit log
        payload_summary = {
            "resource": resource,
            "payload_type": type(payload).__name__,
            "payload_size": len(str(payload)) if payload else 0
        }
        
        audit_log(
            action="mapping_write_blocked",
            actor=actor,
            status="blocked",
            resource_target=resource,
            payload_summary=payload_summary,
            attempted_write=True,
            error_message="Attempted write to protected mapping resource",
            encounter_id=encounter_id
        )
        
        # Notify admin
        notify_admin(
            "Blocked Mapping Write Attempt",
            {
                "actor": actor,
                "resource": resource,
                "timestamp": datetime.utcnow().isoformat(),
                "encounter_id": encounter_id
            }
        )
        
        # Increment blocked write counter (triggers auto-pause if threshold exceeded)
        orchestrator_state.increment_blocked_writes()
        
        # Raise permission error
        raise PermissionError(
            f"Blocked attempt to write to mapping resource: {resource}. "
            "Mapping datastore is READ-ONLY."
        )
    
    # If not a mapping resource, allow the write
    # (actual write logic would be implemented by caller)
    logger.info(f"Write allowed to resource: {resource}")
    return True


def summarize_payload(payload: Any, max_length: int = 200) -> str:
    """
    Create a summary of a payload for logging
    
    Args:
        payload: Payload to summarize
        max_length: Maximum length of summary
        
    Returns:
        Summary string
    """
    try:
        payload_str = json.dumps(payload) if not isinstance(payload, str) else payload
        if len(payload_str) > max_length:
            return payload_str[:max_length] + "..."
        return payload_str
    except:
        return f"<{type(payload).__name__} object>"


# System state management
class OrchestratorState:
    """Manages orchestrator operational state"""
    
    def __init__(self):
        self._mode = "active"  # active, paused, manual
        self._blocked_write_count = 0
        self._last_reset = datetime.utcnow()
    
    def pause(self):
        """Pause orchestrator (emergency stop)"""
        self._mode = "paused"
        logger.warning("Orchestrator PAUSED")
        notify_admin("Orchestrator Paused", {"timestamp": datetime.utcnow().isoformat()})
    
    def resume(self):
        """Resume orchestrator"""
        self._mode = "active"
        logger.info("Orchestrator RESUMED")
    
    def set_manual(self):
        """Set to manual mode (requires human approval for all actions)"""
        self._mode = "manual"
        logger.warning("Orchestrator set to MANUAL mode")
    
    def is_active(self) -> bool:
        """Check if orchestrator is active"""
        return self._mode == "active"
    
    def increment_blocked_writes(self):
        """Increment blocked write counter"""
        self._blocked_write_count += 1
        
        # If too many blocked writes in short time, pause
        if self._blocked_write_count >= 3:
            time_since_reset = (datetime.utcnow() - self._last_reset).total_seconds()
            if time_since_reset < 3600:  # 1 hour
                logger.critical(f"Too many blocked writes ({self._blocked_write_count}) in {time_since_reset}s")
                self.pause()
    
    def reset_blocked_writes(self):
        """Reset blocked write counter"""
        self._blocked_write_count = 0
        self._last_reset = datetime.utcnow()


# Global orchestrator state
orchestrator_state = OrchestratorState()
