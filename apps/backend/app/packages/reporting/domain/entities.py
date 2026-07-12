"""Reporting domain entities — Spec 024."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ReportDefinition:
    id: int
    organization_id: int
    code: str
    title: str
    description: str
    status: str
    default_period: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class ReportGeneration:
    id: int
    organization_id: int
    definition_id: int
    status: str
    period_start: Optional[str]
    period_end: Optional[str]
    filters_json: str
    requested_by: Optional[int]
    requested_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    snapshot_id: Optional[int]


@dataclass
class ReportSnapshot:
    id: int
    organization_id: int
    generation_id: int
    definition_id: int
    payload_json: str
    kpi_versions_json: str
    unavailable_sources_json: str
    limitations: str
    generated_at: datetime
    generated_by: Optional[int]


@dataclass
class ReportSection:
    id: int
    snapshot_id: int
    section_code: str
    title: str
    content_json: str
    sort_order: int


@dataclass
class ReportApproval:
    id: int
    executive_report_id: int
    decision: str
    approved_by: Optional[int]
    approved_at: datetime
    comment: Optional[str]


@dataclass
class ExecutiveReport:
    id: int
    organization_id: int
    definition_id: int
    generation_id: int
    snapshot_id: int
    title: str
    status: str
    period_start: Optional[str]
    period_end: Optional[str]
    published_at: Optional[datetime]
    archived_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class BusinessDecision:
    id: int
    organization_id: int
    executive_report_id: Optional[int]
    title: str
    proposal: str
    status: str
    evidence_refs_json: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class DecisionAction:
    id: int
    decision_id: int
    title: str
    status: str
    assignee_user_id: Optional[int]
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class DecisionFollowUp:
    id: int
    decision_id: int
    note: str
    created_by: Optional[int]
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
