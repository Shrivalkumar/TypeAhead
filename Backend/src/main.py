"""FastAPI application entry point with lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.cache.cache_manager import cache_manager
from src.config import settings
from src.db.batch_writer import batch_writer
from src.db.connection import create_pool, close_pool, pool
from src.middleware.request_logger import RequestLoggerMiddleware
from src.routers import suggest, search, cache_debug, metrics
from src.utils.logger import get_logger, setup_logging
import asyncio

# Initialise structured logging
setup_logging(json_format=False)
logger = get_logger("main")

async def cleanup_old_searches():
    """Periodically remove old rows from recent_searches."""
    while True:
        await asyncio.sleep(settings.trending_cleanup_interval_seconds)
        if pool is not None:
            try:
                # asyncpg returns strings like "DELETE 5"
                result = await pool.execute(
                    f"DELETE FROM recent_searches WHERE searched_at < NOW() - INTERVAL '{settings.trending_window_minutes} minutes'"
                )
                logger.info("trending_cleanup", result=result)
            except Exception as e:
                logger.error("trending_cleanup_failed", error=str(e))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks for the application.

    Startup: initialise DB pool, Redis connections, background tasks.
    Shutdown: flush batch writer, close connections gracefully.
    """
    logger.info("server_starting", host=settings.host, port=settings.port)

    # --- Startup ---
    await create_pool()
    await cache_manager.init()
    batch_writer.start()
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_searches())

    logger.info("server_started")
    yield

    # --- Shutdown ---
    logger.info("server_shutting_down")
    cleanup_task.cancel()
    await batch_writer.stop()
    await cache_manager.close()
    await close_pool()
    logger.info("server_stopped")


app = FastAPI(
    title="TypedAhead",
    description="Search Typeahead System — suggestions, search, distributed cache, trending, batch writes.",
    version="0.1.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggerMiddleware)

# --- Routers ---
app.include_router(suggest.router, tags=["suggest"])
app.include_router(search.router, tags=["search"])
app.include_router(cache_debug.router, tags=["cache"])
app.include_router(metrics.router, tags=["system"])


# --- Health Check ---
@app.get("/health", tags=["system"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}
