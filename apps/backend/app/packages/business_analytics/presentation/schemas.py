"""Business analytics Pydantic schemas — Spec 023."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class KpiDefinitionOut(BaseModel):
    id: int
    code: str
    name: str
    formula_description: str
    version: int
    granularity: str
    frequency: str
    owner_role: Optional[str] = None
    null_handling: str
    source_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class KpiSnapshotOut(BaseModel):
    id: int
    kpi_definition_id: int
    organization_id: Optional[int] = None
    period: str
    value: Optional[float] = None
    quality_status: str
    source_label: str
    is_synthetic: bool
    created_at: datetime


class MetricSourceOut(BaseModel):
    id: int
    code: str
    label: str
    origin_system: str
    description: Optional[str] = None
    created_at: datetime


class DataQualityResultOut(BaseModel):
    id: int
    check_code: str
    organization_id: Optional[int] = None
    status: str
    details: Optional[str] = None
    measured_at: datetime
    created_at: datetime


class BusinessAlertOut(BaseModel):
    id: int
    organization_id: int
    severity: str
    title: str
    body: str
    status: str
    kpi_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BusinessAlertCreateRequest(BaseModel):
    severity: str
    title: str
    body: str
    kpi_code: Optional[str] = None


class RecommendationOut(BaseModel):
    id: int
    organization_id: int
    rule_code: str
    title: str
    rationale: str
    evidence_ref: Optional[str] = None
    is_ai: bool
    created_at: datetime


class DashboardOverviewOut(BaseModel):
    organization_id: int
    period: str
    kpis: dict[str, Any]
    recurring_revenue: Optional[dict[str, Any]] = None
    trends_stub: dict[str, Any]
    comparatives_stub: dict[str, Any]


class DrillDownOut(BaseModel):
    dimension: str
    organization_id: int
    items: Optional[list[dict[str, Any]]] = None
    engagement: Optional[dict[str, Any]] = None
    campaigns: Optional[list[dict[str, Any]]] = None
    message: Optional[str] = None


class CaptureSnapshotRequest(BaseModel):
    kpi_code: str
    period: str
    is_synthetic: bool = False


class StrategicKpiPeriodOut(BaseModel):
    id: Optional[int] = None
    organization_id: Optional[int] = None
    objective_code: str
    kpi_code: str
    period_start: Any
    period_end: Any
    value: Optional[float] = None
    unit: str
    source_label: str
    quality_status: str
    is_synthetic: bool = False
    is_proxy: bool = False
    availability_status: str
    unavailable_reason: Optional[str] = None
    computed_at: Optional[datetime] = None
    classification: Optional[str] = None


class StrategicObjectiveOut(BaseModel):
    objective_code: str
    title: str
    kpi: Optional[dict[str, Any]] = None
    kpis: list[dict[str, Any]] = Field(default_factory=list)
    period_start: str
    period_end: str
    evidence_path: Optional[str] = None
    report_path: Optional[str] = None
    decision_path: Optional[str] = None
    trend: Optional[dict[str, Any]] = None
    empty: bool = False


class StrategicDecisionCapabilityOut(BaseModel):
    can_create_decision: bool = False
    can_draft_report: bool = False
    can_refresh_strategic: bool = False
    is_ai: bool = False
    recommendation_mode: str = "rule_based"


class StrategicOverviewOut(BaseModel):
    organization_id: int
    period_start: str
    period_end: str
    include_global: bool = False
    comparable_periods: int = 0
    objectives: list[StrategicObjectiveOut]
    decision_capability: StrategicDecisionCapabilityOut


class StrategicRefreshOut(BaseModel):
    organization_id: Optional[int] = None
    period_start: str
    period_end: str
    include_global: bool = False
    rows_written: int
