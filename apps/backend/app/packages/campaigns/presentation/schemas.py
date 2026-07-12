"""Campaigns Pydantic schemas — Spec 022."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CampaignCreateRequest(BaseModel):
    name: str
    market: Optional[str] = None
    segment: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    artist_profile_id: Optional[int] = None
    catalog_release_id: Optional[int] = None


class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    market: Optional[str] = None
    segment: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    artist_profile_id: Optional[int] = None
    catalog_release_id: Optional[int] = None


class CampaignOut(BaseModel):
    id: int
    organization_id: int
    name: str
    status: str
    market: Optional[str] = None
    segment: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    artist_profile_id: Optional[int] = None
    catalog_release_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PaginatedCampaigns(BaseModel):
    items: list[CampaignOut]
    total: int
    page: int
    page_size: int


class CampaignObjectiveCreateRequest(BaseModel):
    objective_type: str
    description: Optional[str] = None
    priority: int = 1


class CampaignObjectiveOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    objective_type: str
    description: Optional[str] = None
    priority: int
    created_at: datetime
    updated_at: datetime


class CampaignTargetSetRequest(BaseModel):
    metric_code: str
    target_value: float
    unit: str = "count"


class CampaignTargetOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    metric_code: str
    target_value: float
    unit: str
    created_at: datetime
    updated_at: datetime


class CampaignBudgetSetRequest(BaseModel):
    amount: float = Field(gt=0)
    currency: str
    approval_threshold: Optional[float] = None


class CampaignBudgetOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    amount: float
    currency: str
    approval_threshold: Optional[float] = None
    override_approved: bool
    override_reason: Optional[str] = None
    override_by: Optional[int] = None
    override_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CampaignApprovalSubmitRequest(BaseModel):
    approval_type: str = "launch"


class CampaignApprovalDecideRequest(BaseModel):
    approved: bool
    reason: Optional[str] = None


class CampaignApprovalOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    approval_type: str
    status: str
    requested_by: int
    decided_by: Optional[int] = None
    decision_reason: Optional[str] = None
    requested_at: datetime
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CampaignExpenseCreateRequest(BaseModel):
    amount: float = Field(gt=0)
    currency: str
    category: str
    expense_date: date
    description: Optional[str] = None
    override_id: Optional[int] = None


class CampaignExpenseOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    amount: float
    currency: str
    category: str
    description: Optional[str] = None
    expense_date: date
    recorded_by: int
    override_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CampaignResultCreateRequest(BaseModel):
    metric_code: str
    value: float
    unit: str = "count"
    is_monetary: bool = False
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    source_label: Optional[str] = None


class CampaignResultOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    metric_code: str
    value: float
    unit: str
    is_monetary: bool
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    source_label: Optional[str] = None
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime


class AttributionDefinitionCreateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_code: str
    confidence: float = Field(ge=0, le=1)
    responsible: str
    description: Optional[str] = None


class AttributionDefinitionOut(BaseModel):
    model_config = {"protected_namespaces": ()}
    id: int
    campaign_id: int
    organization_id: int
    version: int
    model_code: str
    description: Optional[str] = None
    confidence: float
    responsible: str
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AttributableRevenueCreateRequest(BaseModel):
    attribution_definition_id: int
    amount: float = Field(gt=0)
    currency: str
    period_start: date
    period_end: date


class AttributableRevenueOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    attribution_definition_id: int
    amount: float
    currency: str
    period_start: date
    period_end: date
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CampaignRoiSnapshotOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    attribution_definition_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    currency: Optional[str] = None
    status: str
    roi_value: Optional[float] = None
    unavailable_reason: Optional[str] = None
    cost_per_result: Optional[float] = None
    budget_utilization: Optional[float] = None
    goal_attainment: Optional[float] = None
    engagement_lift: Optional[float] = None
    computed_at: datetime
    computed_by: Optional[int] = None
    created_at: datetime


class CampaignStatusHistoryOut(BaseModel):
    id: int
    campaign_id: int
    organization_id: int
    from_status: Optional[str] = None
    to_status: str
    reason: Optional[str] = None
    actor_user_id: Optional[int] = None
    at: datetime
    created_at: datetime


class CampaignTransitionRequest(BaseModel):
    reason: Optional[str] = None
