from src.config import settings
from src.db import connection
from src.utils.logger import get_logger

logger = get_logger("trending_service")

async def get_trending_suggestions(prefix: str) -> list[dict]:
    """Fetch top 10 suggestions using the recency-aware trending formula."""
    if not prefix or not prefix.strip():
        return []

    prefix = prefix.lower().strip()
    escaped = prefix.replace("%", "\\%").replace("_", "\\_")

    if connection.pool is None:
        raise RuntimeError("Database pool is not initialized")

    rows = await connection.pool.fetch(
        f"""
        SELECT 
            q.query, 
            q.count AS all_time_count,
            COALESCE(r.recent_count, 0) AS recent_count,
            ((q.count::numeric * $2::numeric) + (COALESCE(r.recent_count, 0)::numeric * $3::numeric)) AS trending_score
        FROM queries q
        LEFT JOIN (
            SELECT query, COUNT(*) AS recent_count
            FROM recent_searches
            WHERE searched_at >= NOW() - INTERVAL '{settings.trending_window_minutes} minutes'
            GROUP BY query
        ) r ON q.query = r.query
        WHERE q.query LIKE $1 || '%'
        ORDER BY trending_score DESC
        LIMIT 10
        """,
        escaped,
        settings.trending_alpha,
        settings.trending_beta
    )
    
    return [
        {
            "query": r["query"],
            "count": r["all_time_count"],
            "recent_count": r["recent_count"],
            "trending_score": round(float(r["trending_score"]), 2)
        }
        for r in rows
    ]
