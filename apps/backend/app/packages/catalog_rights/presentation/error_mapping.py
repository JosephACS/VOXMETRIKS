"""Catalog rights HTTP error mapping — Spec 021."""

from __future__ import annotations

from fastapi import HTTPException

from app.packages.catalog_rights.domain.errors import (
    ApprovalStateError,
    CatalogRightsError,
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
    OverlapConflictError,
    OwnershipPercentageError,
    ValidationError,
    WarehouseTrackNotFoundError,
)


def http_error(status_code: int, message: str, code: str = "catalog_rights_error") -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_catalog_rights_http(exc: CatalogRightsError) -> None:
    if isinstance(exc, WarehouseTrackNotFoundError):
        raise http_error(404, str(exc), "warehouse_track_not_found")
    if isinstance(exc, NotFoundError):
        raise http_error(404, str(exc), "not_found")
    if isinstance(exc, ApprovalStateError):
        raise http_error(422, str(exc), "approval_state_error")
    if isinstance(exc, InvalidTransitionError):
        raise http_error(422, str(exc), "invalid_transition")
    if isinstance(exc, OwnershipPercentageError):
        raise http_error(422, str(exc), "invalid_ownership_percentage")
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc), "validation_error")
    if isinstance(exc, OverlapConflictError):
        raise http_error(409, str(exc), "overlap_conflict")
    if isinstance(exc, ConflictError):
        raise http_error(409, str(exc), "conflict")
    raise http_error(500, str(exc), "catalog_rights_error")
