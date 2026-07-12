"""CRM domain errors — Spec 017."""

from __future__ import annotations


class CrmError(Exception):
    """Base CRM domain error."""


class NotFoundError(CrmError):
    """Entity not found."""


class PermissionDenied(CrmError):
    """Actor lacks required CRM permission."""


class ValidationError(CrmError):
    """Input violates domain rules."""


class ConflictError(CrmError):
    """Unique constraint or state conflict."""


class StaleDataError(CrmError):
    """Optimistic locking mismatch (row_version)."""


class ImmutableError(CrmError):
    """Attempt to mutate an immutable record (e.g. sent quotation version)."""


class TokenExpiredError(CrmError):
    """Claim token has expired."""


class TokenAlreadyUsedError(CrmError):
    """Claim token has already been consumed."""


class ApprovalRequiredError(CrmError):
    """Action requires manager approval first."""


class ApprovalConflict(CrmError):
    """Approval already exists or in terminal state."""


class ConversionConflict(CrmError):
    """Opportunity already has a completed conversion."""


class PersistenceError(CrmError):
    """Unexpected database error."""
