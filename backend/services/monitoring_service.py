"""
Monitoring Service
Provides Prometheus metrics and health checks
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import text
from models.database import SessionLocal

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for application monitoring and metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get application health status
        
        Returns:
            Health status dict
        """
        session = SessionLocal()
        
        try:
            # Check database connectivity
            db_healthy = True
            db_error = None
            try:
                session.execute(text("SELECT 1"))
            except Exception as e:
                db_healthy = False
                db_error = str(e)
            
            # Get mapping protection status
            mapping_protected = True
            try:
                from services.safeguards import orchestrator_state
                mapping_protected = not orchestrator_state.is_paused()
            except:
                pass
            
            # Calculate uptime
            uptime_seconds = int(time.time() - self.start_time)
            
            status = {
                "status": "healthy" if db_healthy and mapping_protected else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": uptime_seconds,
                "components": {
                    "database": {
                        "status": "healthy" if db_healthy else "unhealthy",
                        "error": db_error
                    },
                    "mapping_protection": {
                        "status": "active" if mapping_protected else "paused",
                        "protected": mapping_protected
                    }
                },
                "metrics": {
                    "total_requests": self.request_count,
                    "total_errors": self.error_count
                }
            }
            
            return status
            
        finally:
            session.close()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get Prometheus-style metrics
        
        Returns:
            Metrics dict
        """
        session = SessionLocal()
        
        try:
            # Get database stats
            stats = {}
            
            tables = [
                'users', 'patients', 'encounters', 'appointments',
                'payment_intents', 'teleconsult_sessions', 'claim_packets',
                'mapping_feedback', 'mapping_proposals', 'audit_logs'
            ]
            
            for table in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    stats[f"{table}_total"] = count
                except:
                    stats[f"{table}_total"] = 0
            
            # Get mapping protection stats
            try:
                from services.safeguards import orchestrator_state, MAPPING_DATA_RESOURCES
                stats['mapping_resources_protected'] = len(MAPPING_DATA_RESOURCES)
                stats['orchestrator_blocked_writes'] = orchestrator_state._blocked_write_count
                stats['orchestrator_active'] = 1 if orchestrator_state.is_active() else 0
            except:
                pass
            
            # Application metrics
            stats['app_uptime_seconds'] = int(time.time() - self.start_time)
            stats['app_requests_total'] = self.request_count
            stats['app_errors_total'] = self.error_count
            
            return stats
            
        finally:
            session.close()
    
    def increment_request(self):
        """Increment request counter"""
        self.request_count += 1
    
    def increment_error(self):
        """Increment error counter"""
        self.error_count += 1


# Global monitoring service instance
_monitoring_service: MonitoringService = None


def get_monitoring_service() -> MonitoringService:
    """Get global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
