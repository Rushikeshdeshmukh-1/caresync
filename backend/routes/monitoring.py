"""
Monitoring & Health Check Routes
Provides health status and metrics endpoints
"""

from fastapi import APIRouter, Response
from backend.services.monitoring_service import get_monitoring_service

router = APIRouter(prefix="/api", tags=["monitoring"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns application health status
    """
    monitoring_service = get_monitoring_service()
    return monitoring_service.get_health_status()


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus format
    """
    monitoring_service = get_monitoring_service()
    metrics = monitoring_service.get_metrics()
    
    # Format as Prometheus text format
    lines = []
    for key, value in metrics.items():
        lines.append(f"# TYPE {key} gauge")
        lines.append(f"{key} {value}")
    
    return Response(content="\n".join(lines), media_type="text/plain")


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes
    
    Returns 200 if app is ready to serve traffic
    """
    monitoring_service = get_monitoring_service()
    health = monitoring_service.get_health_status()
    
    if health["status"] == "healthy":
        return {"ready": True}
    else:
        return Response(status_code=503, content='{"ready": false}')


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes
    
    Returns 200 if app is alive
    """
    return {"alive": True}
