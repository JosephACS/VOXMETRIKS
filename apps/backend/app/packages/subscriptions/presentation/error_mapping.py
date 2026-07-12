"""Map subscriptions domain errors to HTTPException — Spec 018."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException

from app.packages.subscriptions.domain.errors import (
    ActiveSubscriptionExists,
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
    OrgNotActiveError,
    PermissionDenied,
    PersistenceError,
    PlanRetiredError,
    SubscriptionError,
    ValidationError,
)


def http_error(status_code: int, message: str, *, code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_sub_http(exc: Exception) -> NoReturn:
    """Translate subscriptions domain errors to HTTP. Never expose stack traces."""
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, PermissionDenied):
        raise http_error(403, str(exc) or "Forbidden", code="permission_denied") from exc
    if isinstance(exc, NotFoundError):
        raise http_error(404, "Not found", code="not_found") from exc
    if isinstance(exc, PlanRetiredError):
        raise http_error(410, str(exc) or "Plan is no longer available", code="plan_retired") from exc
    if isinstance(exc, ActiveSubscriptionExists):
        raise http_error(409, str(exc) or "Active subscription already exists", code="subscription_conflict") from exc
    if isinstance(exc, ConflictError):
        raise http_error(409, str(exc) or "Conflict", code="conflict") from exc
    if isinstance(exc, OrgNotActiveError):
        raise http_error(422, str(exc) or "Organization not active", code="org_not_active") from exc
    if isinstance(exc, InvalidTransitionError):
        raise http_error(422, str(exc) or "Invalid state transition", code="invalid_transition") from exc
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc) or "Validation failed", code="validation_error") from exc
    if isinstance(exc, PersistenceError):
        raise http_error(503, "Persistence error", code="database_error") from exc
    if isinstance(exc, SubscriptionError):
        raise http_error(400, str(exc) or "Subscriptions error", code="subscription_error") from exc
    raise http_error(500, "Internal error", code="internal_error") from exc
