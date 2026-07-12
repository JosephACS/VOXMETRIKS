"""CS/Support schemas — Spec 025."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OnboardingOut(OrmModel):
    id: int
    organization_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class OnboardingStepOut(OrmModel):
    id: int
    onboarding_id: int
    step_code: str
    title: str
    status: str
    blocked_reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    sort_order: int


class BlockStepRequest(BaseModel):
    reason: str


class HealthSnapshotOut(OrmModel):
    id: int
    organization_id: int
    definition_id: int
    score: Optional[float] = None
    score_state: str
    confidence: Optional[float] = None
    components_json: str
    limitations: str
    generated_at: datetime
    generated_by: Optional[int] = None


class RiskCreateRequest(BaseModel):
    title: str
    description: str = ""
    severity: str = "medium"


class RiskOut(OrmModel):
    id: int
    organization_id: int
    title: str
    status: str
    severity: str
    description: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class InterventionCreateRequest(BaseModel):
    title: str
    risk_id: Optional[int] = None
    assignee_user_id: Optional[int] = None


class InterventionOut(OrmModel):
    id: int
    organization_id: int
    risk_id: Optional[int] = None
    title: str
    status: str
    assignee_user_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RenewalOut(OrmModel):
    id: int
    organization_id: int
    readiness_state: str
    score: Optional[float] = None
    notes: str
    evaluated_at: datetime
    evaluated_by: Optional[int] = None


class ExpansionCreateRequest(BaseModel):
    title: str
    estimated_value: Optional[float] = None
    notes: str = ""


class ExpansionOut(OrmModel):
    id: int
    organization_id: int
    title: str
    status: str
    estimated_value: Optional[float] = None
    notes: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class SupportCaseCreateRequest(BaseModel):
    subject: str
    category: str = "general"
    priority: str = "normal"


class SupportCaseOut(OrmModel):
    id: int
    organization_id: int
    subject: str
    category: str
    priority: str
    status: str
    requester_user_id: Optional[int] = None
    assignee_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AssignRequest(BaseModel):
    assignee_user_id: int


class MessageCreateRequest(BaseModel):
    body: str


class MessageOut(OrmModel):
    id: int
    case_id: int
    author_user_id: Optional[int] = None
    body: str
    is_internal: bool
    created_at: datetime


class SatisfactionRequest(BaseModel):
    score: int
    comment: Optional[str] = None


class SatisfactionOut(OrmModel):
    id: int
    case_id: int
    score: int
    comment: Optional[str] = None
    recorded_by: Optional[int] = None
    recorded_at: datetime


class SlaEventOut(OrmModel):
    id: int
    case_id: int
    policy_id: Optional[int] = None
    event_type: str
    due_at: Optional[datetime] = None
    occurred_at: datetime
    met: Optional[bool] = None
