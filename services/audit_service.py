"""
Audit Service for compliance with India's 2016 EHR Standards
Implements ISO 22600 access control and audit trails
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class AuditLog(Base):
    """Audit log table for ISO 22600 compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_token = Column(String)
    user_id = Column(String)
    resource = Column(String)
    action = Column(String)  # read, create, update, delete
    resource_id = Column(String)
    consent_id = Column(String)
    version = Column(String)
    metadata_json = Column(Text)  # JSON string (renamed from metadata to avoid SQLAlchemy conflict)
    ip_address = Column(String)
    user_agent = Column(String)


class AuditService:
    """Service for audit logging and consent tracking"""
    
    def __init__(self):
        database_url = os.getenv("DATABASE_URL", "sqlite:///./terminology.db")
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def log_access(
        self,
        user_token: str,
        resource: str,
        action: str,
        resource_id: Optional[str] = None,
        consent_id: Optional[str] = None,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ):
        """
        Log access for audit trail (ISO 22600 compliance)
        """
        try:
            session = self.get_session()
            
            # Extract user ID from token (in production, decode JWT)
            user_id = user_token[:20] if user_token else "unknown"
            
            # Merge additional kwargs into metadata
            if metadata is None:
                metadata = {}
            metadata.update({k: v for k, v in kwargs.items() if v is not None})
            
            audit_log = AuditLog(
                id=f"audit-{datetime.utcnow().isoformat()}",
                timestamp=datetime.utcnow(),
                user_token=user_token[:50] if user_token else None,  # Store partial token
                user_id=user_id,
                resource=resource,
                action=action,
                resource_id=resource_id,
                consent_id=consent_id,
                version=version,
                metadata_json=json.dumps(metadata) if metadata else None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            session.add(audit_log)
            session.commit()
            session.close()
            
            logger.info(f"Audit log created: {resource}/{action} by {user_id}")
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
    
    async def log_consent(
        self,
        user_token: str,
        consent_id: str,
        consent_type: str,
        granted: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log consent events for compliance
        """
        await self.log_access(
            user_token=user_token,
            resource="consent",
            action="grant" if granted else "revoke",
            resource_id=consent_id,
            consent_id=consent_id,
            metadata={
                "consent_type": consent_type,
                "granted": granted,
                **(metadata or {})
            }
        )
    
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list:
        """
        Retrieve audit trail for compliance reporting
        """
        try:
            session = self.get_session()
            query = session.query(AuditLog)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if resource:
                query = query.filter(AuditLog.resource == resource)
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            logs = query.order_by(AuditLog.timestamp.desc()).all()
            session.close()
            
            return [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "resource": log.resource,
                    "action": log.action,
                    "resource_id": log.resource_id,
                    "consent_id": log.consent_id,
                    "version": log.version,
                    "metadata": json.loads(log.metadata_json) if log.metadata_json else None
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {str(e)}")
            return []
