"""Customer Success & Support entities — Spec 025."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CustomerOnboarding:
    id: int
    organization_id: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class OnboardingStep:
    id: int
    onboarding_id: int
    step_code: str
    title: str
    status: str
    blocked_reason: Optional[str]
    completed_at: Optional[datetime]
    sort_order: int


@dataclass
class HealthDefinition:
    id: int
    organization_id: Optional[int]
    code: str
    version: int
    name: str
    formula_json: str
    weights_json: str
    null_handling: str
    status: str
    limitations: str
    created_at: datetime


@dataclass
class HealthSnapshot:
    id: int
    organization_id: int
    definition_id: int
    score: Optional[float]
    score_state: str
    confidence: Optional[float]
    components_json: str
    limitations: str
    generated_at: datetime
    generated_by: Optional[int]


@dataclass
class CustomerRisk:
    id: int
    organization_id: int
    title: str
    status: str
    severity: str
    description: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class CustomerIntervention:
    id: int
    organization_id: int
    risk_id: Optional[int]
    title: str
    status: str
    assignee_user_id: Optional[int]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class RenewalReadiness:
    id: int
    organization_id: int
    readiness_state: str
    score: Optional[float]
    notes: str
    evaluated_at: datetime
    evaluated_by: Optional[int]


@dataclass
class ExpansionOpportunity:
    id: int
    organization_id: int
    title: str
    status: str
    estimated_value: Optional[float]
    notes: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class SupportCase:
    id: int
    organization_id: int
    subject: str
    category: str
    priority: str
    status: str
    requester_user_id: Optional[int]
    assignee_user_id: Optional[int]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class SupportMessage:
    id: int
    case_id: int
    author_user_id: Optional[int]
    body: str
    is_internal: bool
    created_at: datetime


@dataclass
class SupportAssignment:
    id: int
    case_id: int
    assignee_user_id: int
    assigned_by: Optional[int]
    assigned_at: datetime


@dataclass
class SupportSlaPolicy:
    id: int
    organization_id: int
    name: str
    priority: str
    response_minutes: int
    resolve_minutes: int
    status: str
    academic_label: str


@dataclass
class SupportSlaEvent:
    id: int
    case_id: int
    policy_id: Optional[int]
    event_type: str
    due_at: Optional[datetime]
    occurred_at: datetime
    met: Optional[bool]


@dataclass
class SupportSatisfaction:
    id: int
    case_id: int
    score: int
    comment: Optional[str]
    recorded_by: Optional[int]
    recorded_at: datetime
