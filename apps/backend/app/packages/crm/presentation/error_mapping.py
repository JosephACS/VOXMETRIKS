"""Map CRM domain errors to HTTPException — Spec 017."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException

from app.packages.crm.domain.errors import (
    ApprovalConflict,
    ApprovalRequiredError,
    ConflictError,
    ConversionConflict,
    CrmError,
    ImmutableError,
    NotFoundError,
    PermissionDenied,
    PersistenceError,
    StaleDataError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    ValidationError,
)


def http_error(status_code: int, message: str, *, code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_crm_http(exc: Exception) -> NoReturn:
    """Translate CRM domain errors to HTTP. Never expose stack traces."""
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, PermissionDenied):
        raise http_error(403, str(exc) or "Forbidden", code="permission_denied") from exc
    if isinstance(exc, NotFoundError):
        raise http_error(404, "Not found", code="not_found") from exc
    if isinstance(exc, TokenAlreadyUsedError):
        raise http_error(410, str(exc) or "Token already used", code="token_used") from exc
    if isinstance(exc, (TokenExpiredError,)):
        raise http_error(410, str(exc) or "Token expired", code="token_expired") from exc
    if isinstance(exc, (ConflictError, ConversionConflict, ApprovalConflict)):
        raise http_error(409, str(exc) or "Conflict", code="conflict") from exc
    if isinstance(exc, ImmutableError):
        raise http_error(409, str(exc) or "Record is immutable", code="immutable") from exc
    if isinstance(exc, StaleDataError):
        raise http_error(409, str(exc) or "Stale data", code="stale_data") from exc
    if isinstance(exc, ApprovalRequiredError):
        raise http_error(422, str(exc) or "Approval required", code="approval_required") from exc
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc) or "Validation failed", code="validation_error") from exc
    if isinstance(exc, PersistenceError):
        raise http_error(503, "Persistence error", code="database_error") from exc
    if isinstance(exc, CrmError):
        raise http_error(400, str(exc) or "CRM error", code="crm_error") from exc
    raise http_error(500, "Internal error", code="internal_error") from exc
