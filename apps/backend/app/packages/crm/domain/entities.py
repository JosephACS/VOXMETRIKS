"""CRM domain entity dataclasses — Spec 017."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional


@dataclass(frozen=True)
class Prospect:
    id: int
    display_name: str
    company_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    source: Optional[str]
    status: str
    owner_user_id: int
    organization_id: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


@dataclass(frozen=True)
class Contact:
    id: int
    full_name: str
    email: Optional[str]
    email_normalized: Optional[str]
    phone: Optional[str]
    company_name: Optional[str]
    linked_user_id: Optional[int]
    created_by: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


@dataclass(frozen=True)
class ProspectContact:
    prospect_id: int
    contact_id: int
    is_primary: bool
    is_decision_maker: bool
    is_signatory: bool
    added_at: datetime


@dataclass(frozen=True)
class Opportunity:
    id: int
    prospect_id: int
    name: str
    description: Optional[str]
    stage: str
    probability: int
    expected_value: Optional[Decimal]
    currency: Optional[str]
    expected_close_date: Optional[date]
    actual_close_date: Optional[date]
    outcome: Optional[str]
    owner_user_id: int
    organization_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


@dataclass(frozen=True)
class OpportunityStageHistory:
    id: int
    opportunity_id: int
    from_stage: Optional[str]
    to_stage: str
    actor_user_id: int
    reason: Optional[str]
    occurred_at: datetime


@dataclass(frozen=True)
class SalesActivity:
    id: int
    activity_type: str
    subject: Optional[str]
    body: Optional[str]
    outcome: Optional[str]
    prospect_id: Optional[int]
    contact_id: Optional[int]
    opportunity_id: Optional[int]
    actor_user_id: int
    scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


@dataclass(frozen=True)
class Quotation:
    id: int
    opportunity_id: int
    status: str
    currency: str
    notes: Optional[str]
    row_version: int
    current_version_no: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


@dataclass(frozen=True)
class QuotationVersion:
    id: int
    quotation_id: int
    version_no: int
    status: str
    subtotal: Decimal
    discount_pct: Decimal
    discount_requires_approval: bool
    total: Decimal
    notes: Optional[str]
    sent_at: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    is_immutable: bool
    created_by: int
    created_at: datetime


@dataclass(frozen=True)
class QuotationItem:
    id: int
    quotation_version_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal
    line_total: Decimal
    plan_code: Optional[str]
    sort_order: int
    created_at: datetime


@dataclass(frozen=True)
class ApprovalRequest:
    id: int
    object_type: str
    object_id: int
    reason: str
    threshold_ref: Optional[str]
    status: str
    requested_by: int
    reviewed_by: Optional[int]
    review_note: Optional[str]
    requested_at: datetime
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CustomerConversion:
    id: int
    opportunity_id: int
    mode: str
    status: str
    organization_id: Optional[int]
    contact_id: Optional[int]
    signatory_user_id: Optional[int]
    claim_token_hash: Optional[str]
    claim_token_expires_at: Optional[datetime]
    claim_consumed_at: Optional[datetime]
    idempotency_key: Optional[str]
    requested_by: int
    completed_at: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


def row_to_dict(columns: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
    return {columns[i]: row[i] for i in range(len(columns))}
