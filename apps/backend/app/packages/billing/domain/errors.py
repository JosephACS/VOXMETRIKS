"""Billing domain errors — Spec 019."""

from __future__ import annotations


class BillingError(Exception):
    """Base billing error."""


class NotFoundError(BillingError):
    """Resource not found."""


class ValidationError(BillingError):
    """Invalid input or business rule violation."""


class ConflictError(BillingError):
    """Uniqueness or state conflict."""


class BillingProfileExistsError(ConflictError):
    """Organization already has a billing profile."""


class InvoiceImmutableError(BillingError):
    """Invoice items cannot be changed after issued."""


class InvalidTransitionError(BillingError):
    """State transition not permitted."""


class LedgerImmutableError(BillingError):
    """Ledger entries cannot be updated or deleted."""


class IdempotencyConflictError(ConflictError):
    """Different data sent for existing idempotency key."""


class InsufficientFundsError(BillingError):
    """Refund or allocation exceeds available amount."""


class ProviderError(BillingError):
    """Payment provider returned an error."""


class CurrencyMismatchError(ValidationError):
    """Invoice currency does not match billing profile."""


class PersistenceError(BillingError):
    """Database-level error."""
