"""Business analytics domain entities — Spec 023."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KpiDefinition:
    id: int
    code: str
    name: str
    formula_description: str
    version: int
    granularity: str
    frequency: str
    owner_role: Optional[str]
    null_handling: str
    source_type: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class KpiSnapshot:
    id: int
    kpi_definition_id: int
    organization_id: Optional[int]
    period: str
    value: Optional[float]
    quality_status: str
    source_label: str
    is_synthetic: bool
    created_at: datetime


@dataclass
class MetricSource:
    id: int
    code: str
    label: str
    origin_system: str
    description: Optional[str]
    created_at: datetime


@dataclass
class DataQualityResult:
    id: int
    check_code: str
    organization_id: Optional[int]
    status: str
    details: Optional[str]
    measured_at: datetime
    created_at: datetime


@dataclass
class BusinessAlert:
    id: int
    organization_id: int
    severity: str
    title: str
    body: str
    status: str
    kpi_code: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class AnalyticsViewPreference:
    id: int
    user_id: int
    organization_id: int
    view_key: str
    payload_json: str
    created_at: datetime
    updated_at: datetime


@dataclass
class RecommendationRecord:
    id: int
    organization_id: int
    rule_code: str
    title: str
    rationale: str
    evidence_ref: Optional[str]
    is_ai: bool
    created_at: datetime
