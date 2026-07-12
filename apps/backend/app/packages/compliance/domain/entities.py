"""Compliance domain entities — Spec 026."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class TermsVersion:
    id: int
    version_code: str
    title: str
    content_summary: str
    effective_at: datetime
    status: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class TermsAcceptance:
    id: int
    terms_version_id: int
    user_id: int
    organization_id: Optional[int]
    accepted_at: datetime
    ip_address: Optional[str]
    created_at: datetime


@dataclass
class ConsentDefinition:
    id: int
    organization_id: Optional[int]
    code: str
    title: str
    description: str
    is_required: bool
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ConsentRecord:
    id: int
    consent_definition_id: int
    user_id: int
    organization_id: Optional[int]
    status: str
    granted_at: Optional[datetime]
    withdrawn_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class DataRequest:
    id: int
    organization_id: int
    requester_user_id: int
    request_type: str
    status: str
    subject_user_id: Optional[int]
    reason: Optional[str]
    requested_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class DataRequestAction:
    id: int
    data_request_id: int
    organization_id: int
    action_type: str
    status: str
    actor_user_id: int
    notes: Optional[str]
    export_uri: Optional[str]
    performed_at: datetime
    created_at: datetime


@dataclass
class RetentionPolicy:
    id: int
    organization_id: int
    data_category: str
    retention_days: int
    status: str
    description: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class RetentionExecution:
    id: int
    retention_policy_id: int
    organization_id: int
    status: str
    records_evaluated: int
    records_blocked: int
    executed_at: datetime
    created_at: datetime


@dataclass
class LegalHold:
    id: int
    organization_id: int
    subject_type: str
    subject_id: str
    status: str
    reason: str
    placed_by: int
    placed_at: datetime
    released_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class SecurityIncident:
    id: int
    organization_id: Optional[int]
    title: str
    severity: str
    status: str
    description: str
    reported_by: int
    reported_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class IncidentAction:
    id: int
    incident_id: int
    organization_id: Optional[int]
    action_type: str
    description: str
    actor_user_id: int
    performed_at: datetime
    created_at: datetime


@dataclass
class SensitiveAccessRecord:
    id: int
    organization_id: Optional[int]
    accessor_user_id: int
    resource_type: str
    resource_id: str
    reason: str
    accessed_at: datetime
    created_at: datetime


@dataclass
class AuditLogEntry:
    id: int
    organization_id: Optional[int]
    actor_user_id: Optional[int]
    action: str
    target_type: str
    target_id: str
    source: str
    result: str
    occurred_at: datetime
