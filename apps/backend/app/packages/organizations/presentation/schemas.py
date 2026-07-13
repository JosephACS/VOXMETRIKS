"""HTTP schemas for organizations API (not domain entities)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class OrganizationCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)
    slug: Optional[str] = None
    organization_type: str = "label"
    legal_name: Optional[str] = None
    country_code: Optional[str] = None
    timezone: str = "UTC"
    default_currency: str = "USD"
    activate: bool = True


class OrganizationUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    legal_name: Optional[str] = None
    organization_type: Optional[str] = None
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    default_currency: Optional[str] = None


class OrganizationOut(BaseModel):
    id: int
    display_name: str
    legal_name: Optional[str] = None
    slug: str
    organization_type: str
    country_code: Optional[str] = None
    timezone: str
    default_currency: str
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    is_demo: bool = False
    is_test: bool = False


class MembershipOut(BaseModel):
    id: int
    organization_id: int
    user_id: int
    status: str
    joined_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    removed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OrganizationCreateResponse(BaseModel):
    organization: OrganizationOut
    membership: MembershipOut
    roles: list[str]
    reused_existing: bool = False
    idempotency_mode: str = "slug_deterministic"


class CurrentOrganizationResponse(BaseModel):
    context: Literal["none", "active", "invalid", "access_revoked"]
    organization: Optional[OrganizationOut] = None
    membership: Optional[MembershipOut] = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    source: Optional[str] = None


class MemberActionRequest(BaseModel):
    action: Literal["suspend", "reactivate", "leave"]


class InvitationCreateRequest(BaseModel):
    email: str
    role_codes: list[str] = Field(min_length=1)
    ttl_days: int = Field(default=7, ge=1, le=30)


class InvitationOut(BaseModel):
    id: int
    organization_id: int
    email_normalized: str
    status: str
    expires_at: datetime
    invited_by: int
    initial_role_code: str
    accepted_by: Optional[int] = None
    accepted_at: Optional[datetime] = None
    revoked_by: Optional[int] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class InvitationCreateResponse(BaseModel):
    invitation_id: int
    expires_at: datetime
    invite_token: Optional[str] = None
    returned_once: bool = True
    delivery_status: str = "not_sent"
    invitation: InvitationOut


class AcceptInvitationResponse(BaseModel):
    organization: OrganizationOut
    membership: MembershipOut


class MemberRolesPutRequest(BaseModel):
    assign: list[str] = Field(default_factory=list)
    revoke: list[str] = Field(default_factory=list)


class RoleOut(BaseModel):
    id: int
    code: str
    display_name: str
    description: str
    scope: str
    is_system: bool
    is_active: bool


class PermissionOut(BaseModel):
    id: int
    code: str
    description: str
    domain: str
    is_active: bool


class AuditEntryOut(BaseModel):
    id: int
    organization_id: Optional[int] = None
    actor_user_id: Optional[int] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    reason: Optional[str] = None
    request_id: Optional[str] = None
    source: str
    result: str
    occurred_at: datetime
    previous_values: Optional[dict[str, Any]] = None
    new_values: Optional[dict[str, Any]] = None


class PageMeta(BaseModel):
    page: int
    limit: int
    total: int


class PaginatedMembers(BaseModel):
    items: list[MembershipOut]
    page: int
    limit: int
    total: int


class PaginatedInvitations(BaseModel):
    items: list[InvitationOut]
    page: int
    limit: int
    total: int


class PaginatedAudit(BaseModel):
    items: list[AuditEntryOut]
    page: int
    limit: int
    total: int


class CloseOrganizationRequest(BaseModel):
    reason: Optional[str] = None
