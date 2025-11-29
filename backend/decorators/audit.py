"""
Audit Decorator
Automatically logs actions to audit_logs table
"""

import json
import logging
from datetime import datetime
from functools import wraps
from typing import Callable, Optional
from sqlalchemy import text
from models.database import SessionLocal

logger = logging.getLogger(__name__)


def audit_action(
    resource: str,
    action: str,
    extract_resource_id: Optional[Callable] = None
):
    """
    Decorator to audit endpoint actions
    
    Args:
        resource: Resource type (e.g., 'encounter', 'prescription')
        action: Action type (e.g., 'create', 'update', 'delete')
        extract_resource_id: Optional function to extract resource_id from response
        
    Example:
        @router.post("/encounters")
        @audit_action(resource="encounter", action="create", 
                      extract_resource_id=lambda result: result.get('id'))
        async def create_encounter(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs (FastAPI injects it)
            request = kwargs.get('request')
            
            # Get actor from request state (set by RBAC middleware)
            actor = getattr(request.state, 'actor', None) if request else None
            
            # Execute the actual function
            try:
                result = await func(*args, **kwargs)
                status = "success"
                error_message = None
            except Exception as e:
                result = None
                status = "failed"
                error_message = str(e)
                # Re-raise the exception
                raise
            finally:
                # Log to audit_logs
                try:
                    session = SessionLocal()
                    
                    # Extract resource_id if function provided
                    resource_id = None
                    if extract_resource_id and result:
                        try:
                            resource_id = extract_resource_id(result)
                        except:
                            pass
                    
                    # Build payload
                    payload = {
                        "args": str(args)[:200],  # Truncate
                        "kwargs_keys": list(kwargs.keys())
                    }
                    
                    # Get IP and user agent from request
                    ip_address = None
                    user_agent = None
                    if request:
                        ip_address = request.client.host if request.client else None
                        user_agent = request.headers.get('user-agent', '')[:200]
                    
                    # Insert audit log
                    insert_query = text("""
                        INSERT INTO audit_logs 
                        (user_id, actor_type, action, resource, resource_id, payload, 
                         ip_address, user_agent, status, error_message, timestamp)
                        VALUES 
                        (:user_id, :actor_type, :action, :resource, :resource_id, :payload,
                         :ip_address, :user_agent, :status, :error_message, :timestamp)
                    """)
                    
                    session.execute(insert_query, {
                        "user_id": actor.actor_id if actor else None,
                        "actor_type": actor.actor_type if actor else "anonymous",
                        "action": action,
                        "resource": resource,
                        "resource_id": str(resource_id) if resource_id else None,
                        "payload": json.dumps(payload),
                        "ip_address": ip_address,
                        "user_agent": user_agent,
                        "status": status,
                        "error_message": error_message,
                        "timestamp": datetime.utcnow()
                    })
                    
                    session.commit()
                    session.close()
                    
                except Exception as audit_error:
                    logger.error(f"Audit logging error: {str(audit_error)}")
                    # Don't fail the request if audit logging fails
            
            return result
        
        return wrapper
    return decorator


def audit_read(resource: str):
    """Decorator for read operations"""
    return audit_action(resource=resource, action="read")


def audit_create(resource: str, extract_id: Optional[Callable] = None):
    """Decorator for create operations"""
    return audit_action(resource=resource, action="create", extract_resource_id=extract_id)


def audit_update(resource: str, extract_id: Optional[Callable] = None):
    """Decorator for update operations"""
    return audit_action(resource=resource, action="update", extract_resource_id=extract_id)


def audit_delete(resource: str, extract_id: Optional[Callable] = None):
    """Decorator for delete operations"""
    return audit_action(resource=resource, action="delete", extract_resource_id=extract_id)
