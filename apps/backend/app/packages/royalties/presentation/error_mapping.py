"""Royalty HTTP error mapping — Spec 030."""

from __future__ import annotations

from fastapi import HTTPException

from app.packages.royalties.domain.errors import (
    B2BRequiresManualAttributionError,
    ConflictError,
    CurrencyMismatchError,
    IdempotencyConflictError,
    InvalidTransitionError,
    NotFoundError,
    OwnershipSumError,
    PoolNotApprovedError,
    RoyaltyError,
    SettlementFinalizedError,
    SettlementNotApprovedError,
    StreamsWithoutPoolError,
    ValidationError,
)


def http_error(status_code: int, message: str, code: str = "royalty_error") -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_royalty_http(exc: RoyaltyError) -> None:
    if isinstance(exc, NotFoundError):
        raise http_error(404, str(exc), "not_found")
    if isinstance(exc, OwnershipSumError):
        raise http_error(409, str(exc), "ownership_sum_error")
    if isinstance(exc, PoolNotApprovedError):
        raise http_error(409, str(exc), "pool_not_approved")
    if isinstance(exc, B2BRequiresManualAttributionError):
        raise http_error(409, str(exc), "b2b_requires_manual_attribution")
    if isinstance(exc, StreamsWithoutPoolError):
        raise http_error(409, str(exc), "streams_without_pool")
    if isinstance(exc, SettlementFinalizedError):
        raise http_error(409, str(exc), "settlement_finalized")
    if isinstance(exc, SettlementNotApprovedError):
        raise http_error(409, str(exc), "settlement_not_approved")
    if isinstance(exc, CurrencyMismatchError):
        raise http_error(422, str(exc), "currency_mismatch")
    if isinstance(exc, InvalidTransitionError):
        raise http_error(422, str(exc), "invalid_transition")
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc), "validation_error")
    if isinstance(exc, IdempotencyConflictError):
        raise http_error(409, str(exc), "idempotency_conflict")
    if isinstance(exc, ConflictError):
        raise http_error(409, str(exc), "conflict")
    raise http_error(500, str(exc), "royalty_error")
