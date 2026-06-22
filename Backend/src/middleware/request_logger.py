"""ASGI middleware that logs every request with method, path, status, and duration."""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logger import get_logger

logger = get_logger("http")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Logs each HTTP request with timing information."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter_ns()
        response = await call_next(request)
        duration_ms = (time.perf_counter_ns() - start) / 1_000_000

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) if request.query_params else None,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response
