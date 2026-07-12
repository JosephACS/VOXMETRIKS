"""Billing domain entities — Spec 019."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class BillingProfile:
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


@dataclass
class Invoice:
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


@dataclass
class InvoiceItem:
    id: int
    invoice_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    period_start: Optional[date]
    period_end: Optional[date]
    created_at: datetime


@dataclass
class PaymentMethodReference:
    id: int
    organization_id: int
    provider_code: str
    display_label: str
    token_ref: str
    method_type: str
    is_default: bool
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class PaymentAttempt:
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
    created_at: datetime
    updated_at: datetime


@dataclass
class Payment:
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


@dataclass
class PaymentAllocation:
    id: int
    payment_id: int
    invoice_id: int
    organization_id: int
    amount: Decimal
    created_at: datetime


@dataclass
class Refund:
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


@dataclass
class CreditNote:
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


@dataclass
class PaymentProviderEvent:
    id: int
    provider_code: str
    provider_event_id: str
    event_type: str
    payload: Optional[str]
    processed: bool
    processed_at: Optional[datetime]
    created_at: datetime


@dataclass
class BillingLedgerEntry:
    id: int
    organization_id: int
    entry_type: str
    reference_type: str
    reference_id: int
    amount: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime
