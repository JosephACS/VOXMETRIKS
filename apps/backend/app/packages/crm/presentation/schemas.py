"""CRM Pydantic request/response schemas — Spec 017."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    page: int
    limit: int
    total: int


# ── Prospect ──────────────────────────────────────────────────────────────────

class ProspectCreateRequest(BaseModel):
    display_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class ProspectUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class ProspectStatusRequest(BaseModel):
    status: str


class ProspectOut(BaseModel):
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

    class Config:
        from_attributes = True


class PaginatedProspects(PaginatedResponse):
    items: List[ProspectOut]


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactCreateRequest(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None


class ContactUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None


class ContactOut(BaseModel):
    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    company_name: Optional[str]
    linked_user_id: Optional[int]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedContacts(PaginatedResponse):
    items: List[ContactOut]


class LinkContactRequest(BaseModel):
    contact_id: int
    is_primary: bool = False
    is_decision_maker: bool = False
    is_signatory: bool = False


class ProspectContactOut(BaseModel):
    prospect_id: int
    contact_id: int
    is_primary: bool
    is_decision_maker: bool
    is_signatory: bool
    added_at: datetime


# ── Opportunity ───────────────────────────────────────────────────────────────

class OpportunityCreateRequest(BaseModel):
    prospect_id: int
    name: str
    description: Optional[str] = None
    expected_value: Optional[Decimal] = None
    currency: Optional[str] = None
    probability: int = Field(default=0, ge=0, le=100)
    expected_close_date: Optional[date] = None


class OpportunityUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    expected_value: Optional[Decimal] = None
    currency: Optional[str] = None
    probability: Optional[int] = Field(default=None, ge=0, le=100)
    expected_close_date: Optional[date] = None


class OpportunityStageRequest(BaseModel):
    stage: str
    reason: Optional[str] = None


class OpportunityCloseRequest(BaseModel):
    outcome: str
    stage: str = "closed_won"
    reason: Optional[str] = None


class OpportunityOut(BaseModel):
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

    class Config:
        from_attributes = True


class StageHistoryOut(BaseModel):
    id: int
    opportunity_id: int
    from_stage: Optional[str]
    to_stage: str
    actor_user_id: int
    reason: Optional[str]
    occurred_at: datetime


class PaginatedOpportunities(PaginatedResponse):
    items: List[OpportunityOut]


# ── Sales Activity ────────────────────────────────────────────────────────────

class ActivityCreateRequest(BaseModel):
    activity_type: str
    subject: Optional[str] = None
    body: Optional[str] = None
    prospect_id: Optional[int] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class ActivityUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    outcome: Optional[str] = None
    status: Optional[str] = None
    completed_at: Optional[datetime] = None


class ActivityOut(BaseModel):
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

    class Config:
        from_attributes = True


class PaginatedActivities(PaginatedResponse):
    items: List[ActivityOut]


# ── Quotation ─────────────────────────────────────────────────────────────────

class QuotationCreateRequest(BaseModel):
    opportunity_id: int
    currency: str = Field(min_length=3, max_length=3)
    notes: Optional[str] = None


class QuotationOut(BaseModel):
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

    class Config:
        from_attributes = True


class PaginatedQuotations(PaginatedResponse):
    items: List[QuotationOut]


class QuotationVersionCreateRequest(BaseModel):
    notes: Optional[str] = None


class QuotationVersionOut(BaseModel):
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

    class Config:
        from_attributes = True


class QuotationItemCreateRequest(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    plan_code: Optional[str] = None
    sort_order: int = 0


class QuotationItemOut(BaseModel):
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

    class Config:
        from_attributes = True


class DiscountApprovalRequest(BaseModel):
    reason: str


class SendVersionRequest(BaseModel):
    pass


# ── Approval ──────────────────────────────────────────────────────────────────

class ApprovalReviewRequest(BaseModel):
    review_note: Optional[str] = None


class ApprovalOut(BaseModel):
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

    class Config:
        from_attributes = True


class PaginatedApprovals(PaginatedResponse):
    items: List[ApprovalOut]


# ── Customer Conversion ───────────────────────────────────────────────────────

class ConversionPrepareRequest(BaseModel):
    opportunity_id: int
    mode: str
    contact_id: Optional[int] = None
    idempotency_key: Optional[str] = None


class ConversionOut(BaseModel):
    id: int
    opportunity_id: int
    mode: str
    status: str
    organization_id: Optional[int]
    contact_id: Optional[int]
    signatory_user_id: Optional[int]
    claim_token_expires_at: Optional[datetime]
    claim_consumed_at: Optional[datetime]
    idempotency_key: Optional[str]
    requested_by: int
    completed_at: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversionPrepareResponse(BaseModel):
    conversion: ConversionOut
    claim_token: Optional[str] = None
    claim_token_note: Optional[str] = None


class ConfirmLinkRequest(BaseModel):
    organization_id: int


class ClaimConversionRequest(BaseModel):
    token: str
    org_display_name: str
    org_slug: str
    org_type: str = "prospect"
    timezone: str = "UTC"
    default_currency: str = "USD"
    country_code: Optional[str] = None


class PaginatedConversions(PaginatedResponse):
    items: List[ConversionOut]


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditEntryOut(BaseModel):
    id: int
    organization_id: Optional[int]
    actor_user_id: Optional[int]
    action: str
    target_type: str
    target_id: Optional[str]
    source: str
    result: str
    reason: Optional[str]
    occurred_at: datetime
    previous_values: Optional[Any]
    new_values: Optional[Any]


class PaginatedAudit(PaginatedResponse):
    items: List[AuditEntryOut]
