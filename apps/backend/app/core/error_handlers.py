"""Global FastAPI exception handlers — uniform error envelope, no stack traces in prod."""

from __future__ import annotations

import asyncio
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger("voxmetrik.errors")


def _error_body(
    message: str,
    *,
    status_code: int,
    code: str = "error",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "error",
        "message": message,
        "details": details or {"code": code, "status_code": status_code},
    }


def _safe_message(exc: Exception, *, fallback: str) -> str:
    settings = get_settings()
    if settings.is_production:
        return fallback
    return str(exc) or fallback


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    logger.warning("app_error code=%s message=%s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.message, status_code=exc.status_code, code=exc.code, details=exc.details),
    )


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "Request failed")
        details = detail
    elif isinstance(detail, list):
        message = "Validation failed"
        details = {"errors": detail}
    else:
        message = str(detail)
        details = {"code": "http_error"}
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(message, status_code=exc.status_code, code="http_error", details=details),
    )


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    logger.warning("validation_error count=%s", len(errors))
    return JSONResponse(
        status_code=422,
        content=_error_body(
            "Request validation failed",
            status_code=422,
            code="validation_error",
            details={"errors": errors},
        ),
    )


async def duckdb_exception_handler(_request: Request, exc: duckdb.Error) -> JSONResponse:
    logger.error("duckdb_error type=%s", type(exc).__name__, exc_info=True)
    message = _safe_message(exc, fallback="Database query failed")
    return JSONResponse(
        status_code=503,
        content=_error_body(message, status_code=503, code="database_error"),
    )


async def timeout_exception_handler(_request: Request, exc: asyncio.TimeoutError) -> JSONResponse:
    logger.warning("request_timeout")
    return JSONResponse(
        status_code=504,
        content=_error_body("Request timed out", status_code=504, code="timeout"),
    )


async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("value_error detail=%s", exc)
    return JSONResponse(
        status_code=400,
        content=_error_body(str(exc), status_code=400, code="bad_request"),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception method=%s path=%s",
        request.method,
        request.url.path,
    )
    message = _safe_message(exc, fallback="An unexpected error occurred")
    return JSONResponse(
        status_code=500,
        content=_error_body(message, status_code=500, code="internal_error"),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(duckdb.Error, duckdb_exception_handler)
    app.add_exception_handler(asyncio.TimeoutError, timeout_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
