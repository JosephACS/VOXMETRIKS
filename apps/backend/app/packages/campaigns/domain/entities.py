"""Campaigns domain entities — Spec 022."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Campaign:
    id: int
    organization_id: int
    name: str
    status: str
    market: Optional[str]
    segment: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    artist_profile_id: Optional[int]
    catalog_release_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class CampaignObjective:
    id: int
    campaign_id: int
    organization_id: int
    objective_type: str
    description: Optional[str]
    priority: int
    created_at: datetime
    updated_at: datetime


@dataclass
class CampaignTarget:
    id: int
    campaign_id: int
    organization_id: int
    metric_code: str
    target_value: float
    unit: str
    created_at: datetime
    updated_at: datetime


@dataclass
class CampaignBudget:
    id: int
    campaign_id: int
    organization_id: int
    amount: float
    currency: str
    approval_threshold: Optional[float]
    override_approved: bool
    override_reason: Optional[str]
    override_by: Optional[int]
    override_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class CampaignApproval:
    id: int
    campaign_id: int
    organization_id: int
    approval_type: str
    status: str
    requested_by: int
    decided_by: Optional[int]
    decision_reason: Optional[str]
    requested_at: datetime
    decided_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class CampaignExpense:
    id: int
    campaign_id: int
    organization_id: int
    amount: float
    currency: str
    category: str
    description: Optional[str]
    expense_date: date
    recorded_by: int
    override_id: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class CampaignResult:
    id: int
    campaign_id: int
    organization_id: int
    metric_code: str
    value: float
    unit: str
    is_monetary: bool
    period_start: Optional[date]
    period_end: Optional[date]
    source_label: Optional[str]
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime


@dataclass
class AttributionDefinition:
    id: int
    campaign_id: int
    organization_id: int
    version: int
    model_code: str
    description: Optional[str]
    confidence: float
    responsible: str
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class AttributableRevenueRecord:
    id: int
    campaign_id: int
    organization_id: int
    attribution_definition_id: int
    amount: float
    currency: str
    period_start: date
    period_end: date
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class CampaignRoiSnapshot:
    id: int
    campaign_id: int
    organization_id: int
    attribution_definition_id: Optional[int]
    period_start: Optional[date]
    period_end: Optional[date]
    currency: Optional[str]
    status: str
    roi_value: Optional[float]
    unavailable_reason: Optional[str]
    cost_per_result: Optional[float]
    budget_utilization: Optional[float]
    goal_attainment: Optional[float]
    engagement_lift: Optional[float]
    computed_at: datetime
    computed_by: Optional[int]
    created_at: datetime


@dataclass
class CampaignStatusHistoryEntry:
    id: int
    campaign_id: int
    organization_id: int
    from_status: Optional[str]
    to_status: str
    reason: Optional[str]
    actor_user_id: Optional[int]
    at: datetime
    created_at: datetime
