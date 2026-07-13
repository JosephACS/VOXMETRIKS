from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.rate_limit import check_global_rate_limit

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Baseline security headers for production deployments."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        settings = get_settings()
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """Basic in-memory rate limiting for all API routes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if (
            settings.effective_global_rate_limit > 0
            and request.url.path.startswith(("/api/", "/health"))
        ):
            check_global_rate_limit(
                request,
                max_calls=settings.effective_global_rate_limit,
                window_sec=settings.global_rate_window_sec,
            )
        return await call_next(request)


def configure_security(app: FastAPI) -> None:
    """Apply baseline security middleware (CORS, headers, rate limit)."""
    settings = get_settings()
    origins = settings.cors_origin_list

    if settings.is_production and not origins:
        logger.warning("Production mode without explicit CORS_ORIGINS — cross-origin disabled")

    app.add_middleware(GlobalRateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )
