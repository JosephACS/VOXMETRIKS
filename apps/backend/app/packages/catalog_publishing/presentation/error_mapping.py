"""Catalog publishing HTTP error mapping — Spec 031."""

from __future__ import annotations

from fastapi import HTTPException

from app.packages.catalog_publishing.domain.errors import (
    CatalogPublishingError,
    ConflictError,
    IdempotencyConflictError,
    InvalidTransitionError,
    MediaValidationError,
    NotFoundError,
    RightsGateError,
    SelfApproveError,
    ValidationError,
)


def http_error(status_code: int, message: str, code: str = "publishing_error") -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_publishing_http(exc: CatalogPublishingError) -> None:
    if isinstance(exc, NotFoundError):
        raise http_error(404, str(exc), "not_found")
    if isinstance(exc, SelfApproveError):
        raise http_error(403, str(exc), "self_approve_forbidden")
    if isinstance(exc, RightsGateError):
        raise http_error(409, str(exc), "rights_gate")
    if isinstance(exc, MediaValidationError):
        raise http_error(422, str(exc), "media_validation")
    if isinstance(exc, InvalidTransitionError):
        raise http_error(422, str(exc), "invalid_transition")
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc), "validation_error")
    if isinstance(exc, IdempotencyConflictError):
        raise http_error(409, str(exc), "idempotency_conflict")
    if isinstance(exc, ConflictError):
        raise http_error(409, str(exc), "conflict")
    raise http_error(500, str(exc), "publishing_error")
