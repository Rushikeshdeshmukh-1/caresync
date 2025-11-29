"""
JWT Authentication Service
Handles user registration, login, token generation and validation
"""

import os
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from models.database import User, SessionLocal
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthenticationService:
    """JWT-based authentication service"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def create_access_token(self, user_id: str, email: str, role: str) -> str:
        """
        Create JWT access token
        
        Args:
            user_id: User ID
            email: User email
            role: User role
            
        Returns:
            JWT access token
        """
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        Create JWT refresh token
        
        Args:
            user_id: User ID
            
        Returns:
            JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # Unique token ID
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
    
    def register(
        self,
        email: str,
        password: str,
        name: str,
        role: str = "patient",
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register new user
        
        Args:
            email: User email
            password: Plain text password
            name: User name
            role: User role (patient, doctor, admin)
            phone: Optional phone number
            
        Returns:
            Dict with user info and tokens
        """
        session = SessionLocal()
        
        try:
            # Check if user already exists
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user
            user = User(
                id=str(uuid.uuid4()),
                name=name,
                email=email,
                password_hash=password_hash,
                role=role,
                phone=phone,
                is_active=True,
                email_verified=False,
                created_at=datetime.utcnow()
            )
            
            session.add(user)
            session.commit()
            
            # Generate tokens
            access_token = self.create_access_token(user.id, user.email, user.role)
            refresh_token = self.create_refresh_token(user.id)
            
            logger.info(f"User registered: {email} (role: {role})")
            
            return {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "phone": user.phone
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Registration error: {str(e)}")
            raise
        finally:
            session.close()
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Dict with user info and tokens
        """
        session = SessionLocal()
        
        try:
            # Find user
            user = session.query(User).filter(User.email == email).first()
            
            if not user:
                raise ValueError("Invalid email or password")
            
            if not user.password_hash:
                raise ValueError("User account not properly configured")
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                raise ValueError("Invalid email or password")
            
            if not user.is_active:
                raise ValueError("User account is inactive")
            
            # Update last login
            # user.last_login = datetime.utcnow()
            # session.commit()
            
            # Generate tokens
            access_token = self.create_access_token(user.id, user.email, user.role)
            refresh_token = self.create_refresh_token(user.id)
            
            logger.info(f"User logged in: {email}")
            
            return {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "phone": user.phone
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise
        finally:
            session.close()
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            Dict with new access token
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("sub")
        
        # Get user
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")
            
            # Generate new access token
            access_token = self.create_access_token(user.id, user.email, user.role)
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        finally:
            session.close()
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get current user from token
        
        Args:
            token: JWT access token
            
        Returns:
            User dict if valid, None otherwise
        """
        payload = self.verify_token(token)
        
        if not payload or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                return None
            
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "phone": user.phone
            }
            
        finally:
            session.close()


# Global auth service instance
_auth_service: Optional[AuthenticationService] = None


def get_auth_service() -> AuthenticationService:
    """Get global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from token
    """
    auth_service = get_auth_service()
    user = auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
