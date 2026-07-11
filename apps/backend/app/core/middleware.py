"""Request timing and observability middleware."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.request_context import get_request_id

logger = get_logger("voxmetrik.api")
error_logger = get_logger("voxmetrik.errors")


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Log request/response, duration, and attach X-Response-Time-Ms."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = time.perf_counter()
        req_id = get_request_id()
        user = request.headers.get("Authorization", "")[:20] or None

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            error_logger.exception(
                "request_failed method=%s path=%s elapsed_ms=%s request_id=%s",
                request.method,
                request.url.path,
                elapsed_ms,
                req_id,
            )
            raise

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        if request.url.path.startswith(("/api/", "/health")):
            logger.info(
                "request method=%s path=%s status=%s elapsed_ms=%s request_id=%s user=%s",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
                req_id,
                user,
            )
        return response
