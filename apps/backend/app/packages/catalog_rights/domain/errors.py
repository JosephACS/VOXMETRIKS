"""Catalog rights domain errors — Spec 021."""

from __future__ import annotations


class CatalogRightsError(Exception):
    """Base catalog rights error."""


class NotFoundError(CatalogRightsError):
    """Resource not found."""


class ValidationError(CatalogRightsError):
    """Invalid input or business rule violation."""


class ConflictError(CatalogRightsError):
    """Uniqueness or state conflict."""


class InvalidTransitionError(CatalogRightsError):
    """State transition not permitted."""


class WarehouseTrackNotFoundError(NotFoundError):
    """dim_track reference does not exist."""


class OwnershipPercentageError(ValidationError):
    """A contract party's ownership_percentage is out of range."""


class OverlapConflictError(ConflictError):
    """Adding this party/territory would exceed 100% for an overlapping tuple."""


class ApprovalStateError(ValidationError):
    """Approval workflow invoked out of order (e.g. approve without submit)."""


class PersistenceError(CatalogRightsError):
    """Database-level error."""
