from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any
from services.icd11_service import ICD11Service

router = APIRouter(
    prefix="/api/icd11",
    tags=["ICD-11"],
    responses={404: {"description": "Not found"}},
)

# Initialize service (assuming it's singleton-like or lightweight)
# In a real app, you might use dependency injection or a global instance from main
icd11_service = ICD11Service()

@router.get("/search")
async def search_icd11(q: str = Query(..., min_length=2, description="Search query")):
    """
    Search for ICD-11 entities.
    """
    try:
        results = await icd11_service.search_entities(q)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity/{entity_id:path}")
async def get_icd11_entity(entity_id: str):
    """
    Get details for a specific ICD-11 entity.
    entity_id can be the numeric ID or the full URI.
    """
    try:
        result = await icd11_service.get_entity(entity_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
