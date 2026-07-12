"""Compliance Pydantic schemas — Spec 026."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TermsVersionCreateRequest(BaseModel):
    version_code: str
    title: str
    content_summary: str
    effective_at: datetime


class TermsVersionOut(BaseModel):
    id: int
    version_code: str
    title: str
    content_summary: str
    effective_at: datetime
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PaginatedTermsVersions(BaseModel):
    items: list[TermsVersionOut]
    total: int
    page: int
    page_size: int


class TermsAcceptRequest(BaseModel):
    terms_version_id: int
    ip_address: Optional[str] = None


class TermsAcceptanceOut(BaseModel):
    id: int
    terms_version_id: int
    user_id: int
    organization_id: Optional[int] = None
    accepted_at: datetime
    ip_address: Optional[str] = None
    created_at: datetime


class ConsentDefinitionCreateRequest(BaseModel):
    code: str
    title: str
    description: str
    is_required: bool = False


class ConsentDefinitionOut(BaseModel):
    id: int
    organization_id: Optional[int] = None
    code: str
    title: str
    description: str
    is_required: bool
    status: str
    created_at: datetime
    updated_at: datetime


class PaginatedConsentDefinitions(BaseModel):
    items: list[ConsentDefinitionOut]
    total: int
    page: int
    page_size: int


class ConsentGrantRequest(BaseModel):
    consent_definition_id: int


class ConsentRecordOut(BaseModel):
    id: int
    consent_definition_id: int
    user_id: int
    organization_id: Optional[int] = None
    status: str
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DataRequestSubmitRequest(BaseModel):
    request_type: str = Field(..., pattern="^(access|export|correction|deletion)$")
    subject_user_id: Optional[int] = None
    reason: Optional[str] = None


class DataRequestOut(BaseModel):
    id: int
    organization_id: int
    requester_user_id: int
    request_type: str
    status: str
    subject_user_id: Optional[int] = None
    reason: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaginatedDataRequests(BaseModel):
    items: list[DataRequestOut]
    total: int
    page: int
    page_size: int


class DataRequestActionOut(BaseModel):
    id: int
    data_request_id: int
    organization_id: int
    action_type: str
    status: str
    actor_user_id: int
    notes: Optional[str] = None
    export_uri: Optional[str] = None
    performed_at: datetime
    created_at: datetime


class RetentionPolicyCreateRequest(BaseModel):
    data_category: str
    retention_days: int
    description: Optional[str] = None


class RetentionPolicyOut(BaseModel):
    id: int
    organization_id: int
    data_category: str
    retention_days: int
    status: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class RetentionExecutionOut(BaseModel):
    id: int
    retention_policy_id: int
    organization_id: int
    status: str
    records_evaluated: int
    records_blocked: int
    executed_at: datetime
    created_at: datetime


class LegalHoldCreateRequest(BaseModel):
    subject_type: str
    subject_id: str
    reason: str


class LegalHoldOut(BaseModel):
    id: int
    organization_id: int
    subject_type: str
    subject_id: str
    status: str
    reason: str
    placed_by: int
    placed_at: datetime
    released_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SecurityIncidentCreateRequest(BaseModel):
    title: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    description: str


class SecurityIncidentOut(BaseModel):
    id: int
    organization_id: Optional[int] = None
    title: str
    severity: str
    status: str
    description: str
    reported_by: int
    reported_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaginatedSecurityIncidents(BaseModel):
    items: list[SecurityIncidentOut]
    total: int
    page: int
    page_size: int


class IncidentActionCreateRequest(BaseModel):
    action_type: str
    description: str


class IncidentActionOut(BaseModel):
    id: int
    incident_id: int
    organization_id: Optional[int] = None
    action_type: str
    description: str
    actor_user_id: int
    performed_at: datetime
    created_at: datetime


class SensitiveAccessRequest(BaseModel):
    resource_type: str
    resource_id: str
    reason: str


class SensitiveAccessOut(BaseModel):
    id: int
    organization_id: Optional[int] = None
    accessor_user_id: int
    resource_type: str
    resource_id: str
    reason: str
    accessed_at: datetime
    created_at: datetime


class AuditSearchOut(BaseModel):
    id: int
    organization_id: Optional[int] = None
    actor_user_id: Optional[int] = None
    action: str
    target_type: str
    target_id: str
    source: str
    result: str
    occurred_at: datetime


class PaginatedAuditSearch(BaseModel):
    items: list[AuditSearchOut]
    total: int
    page: int
    page_size: int
