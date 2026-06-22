from fastapi import APIRouter, Query
from src.schemas.models import CacheDebugResponse
from src.cache.cache_manager import cache_manager

router = APIRouter()

@router.get("/cache/debug", response_model=CacheDebugResponse)
async def cache_debug(prefix: str = Query(..., description="Prefix to check in cache")):
    """Get cache debug info for a prefix."""
    info = await cache_manager.debug_info(prefix)
    return CacheDebugResponse(**info)
