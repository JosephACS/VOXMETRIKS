"""Domain and infrastructure exceptions for uniform API error handling."""

from __future__ import annotations


class AppError(Exception):
    """Base application error with HTTP status and optional details."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class DatabaseError(AppError):
    status_code = 503
    code = "database_error"


class RequestTimeoutError(AppError):
    status_code = 504
    code = "timeout"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limit_exceeded"
