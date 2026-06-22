from src.cache.cache_manager import cache_manager
from src.db.batch_writer import batch_writer
from src.utils.logger import get_logger
import asyncio

logger = get_logger("search_service")

async def submit_search(query: str) -> dict:
    """Submit a search query, buffering it in memory for high-throughput batch writes."""
    query = query.lower().strip()
    
    # 1. Add to in-memory buffer
    await batch_writer.record_search(query)
    
    logger.info("search_submitted", query=query)
    return {"message": "Searched"}
