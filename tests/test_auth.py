"""
Tests for Phase 1: Authentication & RBAC
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.jwt_auth_service import AuthenticationService
from backend.middleware.rbac import ActorContext, Roles


class TestAuthenticationService:
    """Test JWT authentication service"""
    
    @pytest.fixture
    def auth_service(self):
        """Create auth service instance"""
        return AuthenticationService()
    
    def test_password_hashing(self, auth_service):
        """Test password hashing and verification"""
        password = "test_password_123"
        
        # Hash password
        hashed = auth_service.hash_password(password)
        
        # Should not be same as plain password
        assert hashed != password
        
        # Should verify correctly
        assert auth_service.verify_password(password, hashed)
        
        # Should not verify wrong password
        assert not auth_service.verify_password("wrong_password", hashed)
    
    def test_create_access_token(self, auth_service):
        """Test access token creation"""
        token = auth_service.create_access_token(
            user_id="test_user_123",
            email="test@example.com",
            role="patient"
        )
        
        # Should return a string token
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation"""
        token = auth_service.create_refresh_token(user_id="test_user_123")
        
        # Should return a string token
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self, auth_service):
        """Test verification of valid token"""
        # Create token
        token = auth_service.create_access_token(
            user_id="test_user_123",
            email="test@example.com",
            role="patient"
        )
        
        # Verify token
        payload = auth_service.verify_token(token)
        
        # Should return payload
        assert payload is not None
        assert payload['sub'] == "test_user_123"
        assert payload['email'] == "test@example.com"
        assert payload['role'] == "patient"
        assert payload['type'] == "access"
    
    def test_verify_invalid_token(self, auth_service):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"
        
        # Should return None
        payload = auth_service.verify_token(invalid_token)
        assert payload is None
    
    def test_token_types(self, auth_service):
        """Test that access and refresh tokens have correct types"""
        access_token = auth_service.create_access_token(
            user_id="test_user",
            email="test@example.com",
            role="patient"
        )
        
        refresh_token = auth_service.create_refresh_token(user_id="test_user")
        
        access_payload = auth_service.verify_token(access_token)
        refresh_payload = auth_service.verify_token(refresh_token)
        
        assert access_payload['type'] == "access"
        assert refresh_payload['type'] == "refresh"


class TestActorContext:
    """Test actor context"""
    
    def test_actor_context_creation(self):
        """Test creating actor context"""
        actor = ActorContext(
            user_id="user_123",
            email="test@example.com",
            role="doctor",
            name="Dr. Test"
        )
        
        assert actor.actor_id == "user_123"
        assert actor.actor_email == "test@example.com"
        assert actor.actor_role == "doctor"
        assert actor.actor_name == "Dr. Test"
        assert actor.actor_type == "user"


class TestRoles:
    """Test role constants"""
    
    def test_role_constants(self):
        """Test that role constants are defined"""
        assert Roles.ADMIN == "admin"
        assert Roles.DOCTOR == "doctor"
        assert Roles.PATIENT == "patient"
        assert Roles.INSURER == "insurer"
        assert Roles.PHARMACIST == "pharmacist"
        assert Roles.NURSE == "nurse"
        assert Roles.STAFF == "staff"


class TestAuthenticationIntegration:
    """Integration tests for authentication flow"""
    
    @pytest.fixture
    def auth_service(self):
        """Create auth service instance"""
        return AuthenticationService()
    
    def test_full_auth_flow(self, auth_service):
        """Test complete authentication flow"""
        # This is a simplified test - actual DB operations would need test database
        
        # 1. Create tokens
        access_token = auth_service.create_access_token(
            user_id="test_user",
            email="test@example.com",
            role="patient"
        )
        
        refresh_token = auth_service.create_refresh_token(user_id="test_user")
        
        # 2. Verify access token
        access_payload = auth_service.verify_token(access_token)
        assert access_payload is not None
        assert access_payload['sub'] == "test_user"
        
        # 3. Verify refresh token
        refresh_payload = auth_service.verify_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload['sub'] == "test_user"
        assert refresh_payload['type'] == "refresh"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
