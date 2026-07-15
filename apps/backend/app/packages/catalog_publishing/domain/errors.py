"""Catalog publishing domain errors — Spec 031."""

from __future__ import annotations


class CatalogPublishingError(Exception):
    """Base catalog-publishing error."""


class NotFoundError(CatalogPublishingError):
    """Resource not found."""


class ValidationError(CatalogPublishingError):
    """Invalid input or business rule violation."""


class ConflictError(CatalogPublishingError):
    """Uniqueness or state conflict."""


class IdempotencyConflictError(ConflictError):
    """Different data sent for existing idempotency key."""


class InvalidTransitionError(CatalogPublishingError):
    """State transition not permitted."""


class RightsGateError(ValidationError):
    """Rights ownership / conflict / period gate failed."""


class MediaValidationError(ValidationError):
    """Media type, size, path, or content rejected."""


class PermissionDeniedError(CatalogPublishingError):
    """Caller lacks publishing permission."""


class SelfApproveError(InvalidTransitionError):
    """Creator cannot approve own submission."""
