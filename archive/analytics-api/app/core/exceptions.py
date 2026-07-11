from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.response_wrapper import structured_error


class AnalyticsError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "ANALYTICS_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
        super().__init__(message)


class DatabaseNotFoundError(AnalyticsError):
    def __init__(self, message: str = "Database not available") -> None:
        super().__init__(message, status_code=503, code="DATABASE_UNAVAILABLE")


class QueryError(AnalyticsError):
    def __init__(
        self,
        message: str = "Query execution failed",
        *,
        code: str = "QUERY_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=500, code=code, details=details)


class ValidationError(AnalyticsError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=422, code="VALIDATION_ERROR", details=details)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AnalyticsError)
    async def analytics_error_handler(request: Request, exc: AnalyticsError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=structured_error(
                exc.message,
                code=exc.code,
                details=exc.details,
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=structured_error(
                "Request validation failed",
                code="REQUEST_VALIDATION_ERROR",
                details={"errors": exc.errors()},
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=structured_error(
                str(exc.detail),
                code="HTTP_ERROR",
                details={"status_code": exc.status_code},
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=structured_error(
                str(exc),
                code="DATABASE_NOT_FOUND",
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=structured_error(
                "Internal server error",
                code="INTERNAL_SERVER_ERROR",
                request_id=_request_id(request),
            ),
        )
