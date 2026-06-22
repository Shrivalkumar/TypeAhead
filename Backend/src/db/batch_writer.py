import asyncio
from collections import defaultdict
from src.cache.cache_manager import cache_manager
from src.db import connection
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("batch_writer")

class BatchWriter:
    """Buffers search queries in memory and flushes them to Postgres periodically."""
    
    def __init__(self):
        self.buffer_lock = asyncio.Lock()
        # buffer structure: {query: count}
        self.query_counts: dict[str, int] = defaultdict(int)
        self.flush_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

    def start(self):
        """Start the background flush task."""
        if self.flush_task is None:
            self.flush_task = asyncio.create_task(self._flush_loop())

    async def stop(self):
        """Stop the flush task and flush remaining buffer."""
        self._shutdown_event.set()
        if self.flush_task:
            # Wait for the loop to notice shutdown and perform final flush
            await self.flush_task

    async def record_search(self, query: str):
        """Add a search to the buffer (O(1) memory operation)."""
        async with self.buffer_lock:
            self.query_counts[query] += 1
            
        # If buffer is getting too large, we could trigger an early flush here,
        # but for simplicity we rely on the periodic flush.

    async def _flush_loop(self):
        """Background loop that periodically flushes the buffer to DB."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for flush interval OR shutdown signal
                await asyncio.wait_for(
                    self._shutdown_event.wait(), 
                    timeout=settings.batch_flush_interval_seconds
                )
            except asyncio.TimeoutError:
                # Timeout means interval elapsed normally
                pass

            await self.flush()

    async def flush(self):
        """Perform the actual DB bulk inserts and updates."""
        async with self.buffer_lock:
            if not self.query_counts:
                return
            
            # Copy and clear buffer fast to release lock
            counts_to_flush = self.query_counts
            self.query_counts = defaultdict(int)

        if connection.pool is None:
            logger.error("flush_failed_no_db_pool")
            return

        total_queries = sum(counts_to_flush.values())
        unique_queries = len(counts_to_flush)
        logger.info("flushing_batch", unique=unique_queries, total=total_queries)

        try:
            async with connection.pool.acquire() as conn:
                async with conn.transaction():
                    # 1. Update historical counts
                    # asyncpg.executemany allows batch execution of parameterized queries.
                    await conn.executemany(
                        """
                        INSERT INTO queries (query, count)
                        VALUES ($1, $2)
                        ON CONFLICT (query) DO UPDATE SET
                            count = queries.count + EXCLUDED.count,
                            updated_at = NOW()
                        """,
                        [(q, c) for q, c in counts_to_flush.items()]
                    )

                    # 2. Update recent_searches for trending
                    # For recent_searches, we insert one row per individual search.
                    # Since counts_to_flush has aggregated counts, we expand them out
                    # so that a query searched 5 times in this window gets 5 rows.
                    recent_records = []
                    for q, c in counts_to_flush.items():
                        recent_records.extend([(q,)] * c)

                    await conn.executemany(
                        "INSERT INTO recent_searches (query, searched_at) VALUES ($1, NOW())",
                        recent_records
                    )
            
            # 3. Invalidate cache for all flushed queries
            for q in counts_to_flush.keys():
                asyncio.create_task(cache_manager.invalidate_prefixes(q))
                
            logger.info("flush_success")
        except Exception as e:
            logger.error("flush_error", error=str(e))
            # On error, we could try to put the items back into the buffer, 
            # but for this scale, dropping the batch is safer than infinitely retrying poisoned data.

# Global singleton
batch_writer = BatchWriter()
