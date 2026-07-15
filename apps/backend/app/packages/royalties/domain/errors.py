"""Royalty domain errors — Spec 030."""

from __future__ import annotations


class RoyaltyError(Exception):
    """Base royalty error."""


class NotFoundError(RoyaltyError):
    """Resource not found."""


class ValidationError(RoyaltyError):
    """Invalid input or business rule violation."""


class ConflictError(RoyaltyError):
    """Uniqueness or state conflict."""


class IdempotencyConflictError(ConflictError):
    """Different data sent for existing idempotency key."""


class InvalidTransitionError(RoyaltyError):
    """State transition not permitted."""


class PoolNotApprovedError(InvalidTransitionError):
    """Settlement requires an approved pool."""


class OwnershipSumError(ValidationError):
    """Rights contract parties do not sum to 100%."""


class B2BRequiresManualAttributionError(ValidationError):
    """B2B income cannot auto-feed a royalty pool."""


class CurrencyMismatchError(ValidationError):
    """Currency does not match pool or settlement."""


class SettlementFinalizedError(InvalidTransitionError):
    """Finalized settlement cannot be destructively edited."""


class SettlementNotApprovedError(InvalidTransitionError):
    """Payout requires an approved/finalized settlement."""


class StreamsWithoutPoolError(ValidationError):
    """Streams cannot become money without approved pool + attribution."""


class PermissionDeniedError(RoyaltyError):
    """Caller lacks royalty permission."""
