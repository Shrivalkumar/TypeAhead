from fastapi import APIRouter
from pydantic import BaseModel
from src.cache.cache_manager import cache_manager
from src.db.batch_writer import batch_writer
from src.db import connection

router = APIRouter()

class MetricsResponse(BaseModel):
    cache_stats: list[dict]
    batch_buffer_size: int
    db_pool_size: int

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Export system metrics for observability."""
    cache_stats = await cache_manager.all_stats()
    
    # Safely get DB pool size
    pool_size = 0
    if connection.pool is not None:
        pool_size = connection.pool.get_size()
        
    return MetricsResponse(
        cache_stats=cache_stats,
        batch_buffer_size=len(batch_writer.query_counts),
        db_pool_size=pool_size
    )
