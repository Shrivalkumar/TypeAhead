from src.cache.cache_manager import cache_manager
from src.db import connection
from src.config import settings
from src.services import trending_service
from src.utils.logger import get_logger
import asyncio

logger = get_logger("suggestion_service")

async def get_suggestions(prefix: str) -> tuple[str, list[dict]]:
    """Fetch top 10 suggestions for a given prefix using cache-aside.
    Returns (ranking_mode, suggestions).
    """
    if not prefix or not prefix.strip():
        return "all_time", []

    prefix = prefix.lower().strip()
    
    # 1. Check cache
    node_id, cached = await cache_manager.get(prefix)
    if cached is not None:
        logger.info("cache_hit", prefix=prefix, node=node_id)
        # We store just the list in cache, but we don't know the mode from the raw cache easily.
        # We can assume if trending is enabled, the cache holds trending results.
        mode = "trending" if settings.trending_enabled else "all_time"
        return mode, cached

    # 2. Cache miss -> query DB
    logger.info("cache_miss", prefix=prefix, node=node_id)
    
    if settings.trending_enabled:
        ranking_mode = "trending"
        results = await trending_service.get_trending_suggestions(prefix)
    else:
        ranking_mode = "all_time"
        escaped = prefix.replace("%", "\\%").replace("_", "\\_")

        if connection.pool is None:
            raise RuntimeError("Database pool is not initialized")

        rows = await connection.pool.fetch(
            """
            SELECT query, count
            FROM queries
            WHERE query LIKE $1 || '%'
            ORDER BY count DESC
            LIMIT 10
            """,
            escaped
        )
        results = [{"query": r["query"], "count": r["count"]} for r in rows]
    
    # 3. Populate cache
    asyncio.create_task(cache_manager.set(prefix, results))
    
    return ranking_mode, results
