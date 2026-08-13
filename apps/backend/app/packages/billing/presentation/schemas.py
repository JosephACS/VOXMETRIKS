"""Billing Pydantic schemas — Spec 019."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


# ── BillingProfile ─────────────────────────────────────────────────────────────

class BillingProfileCreateRequest(BaseModel):
    default_currency: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[str] = None
    email: Optional[str] = None


class BillingProfileUpdateRequest(BaseModel):
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[str] = None
    email: Optional[str] = None


class BillingProfileOut(BaseModel):
    id: int
    organization_id: int
    default_currency: str
    legal_name: Optional[str]
    tax_id: Optional[str]
    billing_address: Optional[str]
    email: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


# ── Invoice ────────────────────────────────────────────────────────────────────

class InvoiceCreateRequest(BaseModel):
    billing_profile_id: int
    subscription_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def period_end_not_before_start(self) -> "InvoiceCreateRequest":
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_end < self.period_start
        ):
            raise ValueError("period_end must be on or after period_start")
        return self


class InvoiceItemAddRequest(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(ge=0)
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    @model_validator(mode="after")
    def period_end_not_before_start(self) -> "InvoiceItemAddRequest":
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_end < self.period_start
        ):
            raise ValueError("period_end must be on or after period_start")
        return self


class InvoiceVoidRequest(BaseModel):
    reason: Optional[str] = None


class InvoiceItemOut(BaseModel):
    id: int
    invoice_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    period_start: Optional[date]
    period_end: Optional[date]
    created_at: datetime


class InvoiceOut(BaseModel):
    id: int
    organization_id: int
    billing_profile_id: int
    subscription_id: Optional[int]
    invoice_number: str
    currency: str
    status: str
    subtotal: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    period_start: Optional[date]
    period_end: Optional[date]
    due_date: Optional[date]
    issued_at: Optional[datetime]
    paid_at: Optional[datetime]
    voided_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class PaginatedInvoices(BaseModel):
    items: List[InvoiceOut]
    total: int
    page: int
    page_size: int


# ── PaymentMethodReference ─────────────────────────────────────────────────────

class PaymentMethodCreateRequest(BaseModel):
    provider_code: str
    display_label: str
    token_ref: str
    method_type: str
    is_default: bool = False


class PaymentMethodOut(BaseModel):
    id: int
    organization_id: int
    provider_code: str
    display_label: str
    method_type: str
    is_default: bool
    status: str
    created_at: datetime
    updated_at: datetime


# ── PaymentAttempt ─────────────────────────────────────────────────────────────

class PaymentAttemptCreateRequest(BaseModel):
    invoice_id: int
    provider_code: str
    idempotency_key: str
    amount: Decimal
    currency: str
    payment_method_ref_id: Optional[int] = None


class PaymentAttemptOut(BaseModel):
    id: int
    organization_id: int
    invoice_id: int
    payment_method_ref_id: Optional[int]
    provider_code: str
    idempotency_key: str
    amount: Decimal
    currency: str
    status: str
    provider_attempt_id: Optional[str]
    failure_reason: Optional[str]
    is_mock: bool
    created_at: datetime
    updated_at: datetime


class PaginatedAttempts(BaseModel):
    items: List[PaymentAttemptOut]
    total: int
    page: int
    page_size: int


# ── Payment ────────────────────────────────────────────────────────────────────

class ManualTransferRequest(BaseModel):
    invoice_id: int
    amount: Decimal
    currency: str
    idempotency_key: Optional[str] = None
    notes: Optional[str] = None


class PaymentAllocateRequest(BaseModel):
    invoice_id: int
    amount: Decimal


class PaymentReverseRequest(BaseModel):
    reason: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    organization_id: int
    payment_attempt_id: int
    provider_code: str
    amount: Decimal
    currency: str
    status: str
    provider_payment_id: Optional[str]
    settled_at: Optional[datetime]
    reconciled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PaymentAllocationOut(BaseModel):
    id: int
    payment_id: int
    invoice_id: int
    organization_id: int
    amount: Decimal
    created_at: datetime


class PaginatedPayments(BaseModel):
    items: List[PaymentOut]
    total: int
    page: int
    page_size: int


# ── Refund ─────────────────────────────────────────────────────────────────────

class RefundCreateRequest(BaseModel):
    payment_id: int
    amount: Decimal
    reason: Optional[str] = None
    idempotency_key: Optional[str] = None


class RefundOut(BaseModel):
    id: int
    organization_id: int
    payment_id: int
    amount: Decimal
    currency: str
    reason: Optional[str]
    status: str
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    idempotency_key: str


class PaginatedRefunds(BaseModel):
    items: List[RefundOut]
    total: int
    page: int
    page_size: int


# ── CreditNote ─────────────────────────────────────────────────────────────────

class CreditNoteCreateRequest(BaseModel):
    invoice_id: int
    amount: Decimal
    reason: Optional[str] = None


class CreditNoteOut(BaseModel):
    id: int
    organization_id: int
    invoice_id: int
    credit_note_number: str
    amount: Decimal
    currency: str
    reason: Optional[str]
    status: str
    issued_at: Optional[datetime]
    applied_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PaginatedCreditNotes(BaseModel):
    items: List[CreditNoteOut]
    total: int
    page: int
    page_size: int


# ── ProviderEvent ──────────────────────────────────────────────────────────────

class ProviderEventRequest(BaseModel):
    provider_code: str
    provider_event_id: str
    event_type: str
    payload: Optional[str] = None
    # Conceptual signature fields — verified when secret configured
    signature: Optional[str] = None


class PaymentAttemptRetryRequest(BaseModel):
    idempotency_key: str


class PaymentAttemptFailRequest(BaseModel):
    failure_reason: Optional[str] = None


class PaymentAttemptSimulateRequest(BaseModel):
    """Demo-only mock outcome. Never real money."""
    scenario: str


class MockSimulateOut(BaseModel):
    attempt: PaymentAttemptOut
    scenario: str
    labeled_mock: bool = True
    message: str
    provider_event: dict


class DunningOut(BaseModel):
    id: int
    organization_id: int
    invoice_id: int
    subscription_id: Optional[int] = None
    status: str
    retry_count: int
    next_retry_at: Optional[datetime] = None
    grace_until: Optional[datetime] = None
    last_error_sanitized: Optional[str] = None
    last_attempt_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PaginatedDunning(BaseModel):
    items: List[DunningOut]
    total: int


class ProviderEventOut(BaseModel):
    id: int
    provider_code: str
    provider_event_id: str
    event_type: str
    processed: bool
    created_at: datetime


# ── Ledger ─────────────────────────────────────────────────────────────────────

class LedgerEntryOut(BaseModel):
    id: int
    organization_id: int
    entry_type: str
    reference_type: str
    reference_id: int
    amount: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime


class PaginatedLedger(BaseModel):
    items: List[LedgerEntryOut]
    total: int
    page: int
    page_size: int
