"""Billing HTTP error mapping — Spec 019."""

from __future__ import annotations

from fastapi import HTTPException

from app.packages.billing.domain.errors import (
    BillingError,
    BillingProfileExistsError,
    ConflictError,
    CurrencyMismatchError,
    IdempotencyConflictError,
    InsufficientFundsError,
    InvalidTransitionError,
    InvoiceImmutableError,
    LedgerImmutableError,
    NotFoundError,
    ValidationError,
)


def http_error(status_code: int, message: str, code: str = "billing_error") -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_billing_http(exc: BillingError) -> None:
    if isinstance(exc, NotFoundError):
        raise http_error(404, str(exc), "not_found")
    if isinstance(exc, BillingProfileExistsError):
        raise http_error(409, str(exc), "billing_profile_exists")
    if isinstance(exc, InvoiceImmutableError):
        raise http_error(409, str(exc), "invoice_immutable")
    if isinstance(exc, LedgerImmutableError):
        raise http_error(409, str(exc), "ledger_immutable")
    if isinstance(exc, InvalidTransitionError):
        raise http_error(422, str(exc), "invalid_transition")
    if isinstance(exc, CurrencyMismatchError):
        raise http_error(422, str(exc), "currency_mismatch")
    if isinstance(exc, InsufficientFundsError):
        raise http_error(422, str(exc), "insufficient_funds")
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc), "validation_error")
    if isinstance(exc, ConflictError):
        raise http_error(409, str(exc), "conflict")
    raise http_error(500, str(exc), "billing_error")
