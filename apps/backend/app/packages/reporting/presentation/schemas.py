"""Reporting Pydantic schemas — Spec 024."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReportDefinitionCreateRequest(BaseModel):
    code: str
    title: str
    description: str = ""
    default_period: str = "last_30d"


class ReportDefinitionOut(BaseModel):
    id: int
    organization_id: int
    code: str
    title: str
    description: str
    status: str
    default_period: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ReportGenerationRequest(BaseModel):
    definition_id: int
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    filters: dict[str, Any] = Field(default_factory=dict)


class ReportGenerationOut(BaseModel):
    id: int
    organization_id: int
    definition_id: int
    status: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    filters_json: str
    requested_by: Optional[int] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    snapshot_id: Optional[int] = None


class ReportSnapshotOut(BaseModel):
    id: int
    organization_id: int
    generation_id: int
    definition_id: int
    payload_json: str
    kpi_versions_json: str
    unavailable_sources_json: str
    limitations: str
    generated_at: datetime
    generated_by: Optional[int] = None


class ExecutiveReportOut(BaseModel):
    id: int
    organization_id: int
    definition_id: int
    generation_id: int
    snapshot_id: int
    title: str
    status: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ApproveReportRequest(BaseModel):
    comment: Optional[str] = None


class GenerateResultOut(BaseModel):
    generation: ReportGenerationOut
    snapshot: ReportSnapshotOut
    executive_report: ExecutiveReportOut


class PaginatedDefinitions(BaseModel):
    items: list[ReportDefinitionOut]
    total: int
    page: int
    page_size: int


class PaginatedExecutiveReports(BaseModel):
    items: list[ExecutiveReportOut]
    total: int
    page: int
    page_size: int


class BusinessDecisionCreateRequest(BaseModel):
    title: str
    proposal: str
    executive_report_id: Optional[int] = None
    evidence_refs: list[Any] = Field(default_factory=list)


class BusinessDecisionOut(BaseModel):
    id: int
    organization_id: int
    executive_report_id: Optional[int] = None
    title: str
    proposal: str
    status: str
    evidence_refs_json: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class DecisionActionCreateRequest(BaseModel):
    title: str
    assignee_user_id: Optional[int] = None


class DecisionActionUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class DecisionActionOut(BaseModel):
    id: int
    decision_id: int
    title: str
    status: str
    assignee_user_id: Optional[int] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DecisionFollowUpCreateRequest(BaseModel):
    note: str


class DecisionFollowUpOut(BaseModel):
    id: int
    decision_id: int
    note: str
    created_by: Optional[int] = None
    created_at: datetime


class PaginatedDecisions(BaseModel):
    items: list[BusinessDecisionOut]
    total: int
    page: int
    page_size: int
