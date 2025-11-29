"""
Authentication Routes
Handles user registration, login, token refresh, and logout
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from backend.services.jwt_auth_service import get_auth_service
from backend.middleware.rbac import get_current_user, ActorContext, require_auth
from backend.decorators.audit import audit_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "patient"  # patient, doctor
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    user: dict
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    phone: Optional[str] = None


# Routes
@router.post("/register", response_model=AuthResponse)
@audit_action(resource="user", action="register", extract_resource_id=lambda r: r.get('user', {}).get('id'))
async def register(request: Request, data: RegisterRequest):
    """
    Register new user account
    
    - **email**: User email (must be unique)
    - **password**: Password (min 8 characters recommended)
    - **name**: Full name
    - **role**: User role (patient or doctor)
    - **phone**: Optional phone number
    """
    try:
        auth_service = get_auth_service()
        
        # Validate role
        allowed_roles = ["patient", "doctor"]
        if data.role not in allowed_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Allowed roles: {', '.join(allowed_roles)}"
            )
        
        # Register user
        result = auth_service.register(
            email=data.email,
            password=data.password,
            name=data.name,
            role=data.role,
            phone=data.phone
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
@audit_action(resource="user", action="login", extract_resource_id=lambda r: r.get('user', {}).get('id'))
async def login(request: Request, data: LoginRequest):
    """
    Login with email and password
    
    Returns JWT access token and refresh token
    """
    try:
        auth_service = get_auth_service()
        
        result = auth_service.login(
            email=data.email,
            password=data.password
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    Returns new access token
    """
    try:
        auth_service = get_auth_service()
        
        result = auth_service.refresh_access_token(data.refresh_token)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout")
@audit_action(resource="user", action="logout")
async def logout(request: Request, actor: ActorContext = Depends(require_auth)):
    """
    Logout current user
    
    (In stateless JWT, this is mainly for audit logging.
     Client should discard tokens.)
    """
    return {
        "message": "Logged out successfully",
        "user_id": actor.actor_id
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(actor: ActorContext = Depends(require_auth)):
    """
    Get current authenticated user information
    """
    return {
        "id": actor.actor_id,
        "name": actor.actor_name,
        "email": actor.actor_email,
        "role": actor.actor_role,
        "phone": None  # TODO: fetch from database if needed
    }


@router.get("/verify")
async def verify_token(actor: ActorContext = Depends(require_auth)):
    """
    Verify if current token is valid
    """
    return {
        "valid": True,
        "user_id": actor.actor_id,
        "role": actor.actor_role
    }
