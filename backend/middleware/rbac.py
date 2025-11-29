"""
Role-Based Access Control (RBAC) Middleware
Provides role checking and actor context for requests
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Callable
from functools import wraps
import logging

from backend.services.jwt_auth_service import get_auth_service

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class ActorContext:
    """Actor context attached to requests"""
    
    def __init__(self, user_id: str, email: str, role: str, name: str = None):
        self.actor_id = user_id
        self.actor_email = email
        self.actor_role = role
        self.actor_name = name
        self.actor_type = "user"


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[ActorContext]:
    """
    Get current user from JWT token
    
    Args:
        request: FastAPI request
        credentials: HTTP Bearer credentials
        
    Returns:
        ActorContext if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    auth_service = get_auth_service()
    
    # Verify token
    payload = auth_service.verify_token(token)
    
    if not payload:
        return None
    
    # Get user details
    user = auth_service.get_current_user(token)
    
    if not user:
        return None
    
    # Create actor context
    actor = ActorContext(
        user_id=user['id'],
        email=user['email'],
        role=user['role'],
        name=user.get('name')
    )
    
    # Attach to request state
    request.state.actor = actor
    
    return actor


async def require_auth(
    actor: Optional[ActorContext] = Depends(get_current_user)
) -> ActorContext:
    """
    Require authentication
    
    Args:
        actor: Actor context from get_current_user
        
    Returns:
        ActorContext
        
    Raises:
        HTTPException: If not authenticated
    """
    if not actor:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return actor


def require_role(*allowed_roles: str):
    """
    Decorator to require specific role(s)
    
    Args:
        *allowed_roles: Allowed roles (e.g., 'doctor', 'admin')
        
    Returns:
        Dependency function
        
    Example:
        @router.get("/admin/users")
        async def get_users(actor: ActorContext = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(actor: ActorContext = Depends(require_auth)) -> ActorContext:
        if actor.actor_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return actor
    
    return role_checker


def require_any_role(*allowed_roles: str):
    """
    Decorator to require any of the specified roles
    Alias for require_role for clarity
    """
    return require_role(*allowed_roles)


def require_all_roles(*required_roles: str):
    """
    Decorator to require all of the specified roles
    (For future multi-role support)
    """
    # For now, same as require_role since users have single role
    return require_role(*required_roles)


async def get_optional_actor(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[ActorContext]:
    """
    Get actor context if authenticated, None otherwise (no error)
    
    Args:
        request: FastAPI request
        credentials: HTTP Bearer credentials
        
    Returns:
        ActorContext if authenticated, None otherwise
    """
    try:
        return await get_current_user(request, credentials)
    except Exception as e:
        logger.debug(f"Optional auth failed: {str(e)}")
        return None


# Role constants for easy reference
class Roles:
    """Role constants"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    INSURER = "insurer"
    PHARMACIST = "pharmacist"
    NURSE = "nurse"
    STAFF = "staff"
