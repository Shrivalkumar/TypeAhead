import asyncpg
from src.config import settings

# Global pool instance
pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    """Create and return an asyncpg connection pool."""
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=settings.db_pool_min,
            max_size=settings.db_pool_max,
        )
    return pool


async def close_pool() -> None:
    """Close the global asyncpg connection pool."""
    global pool
    if pool is not None:
        await pool.close()
        pool = None
