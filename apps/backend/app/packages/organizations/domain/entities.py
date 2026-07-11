"""Internal entity dataclasses (not HTTP schemas)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class Organization:
    id: int
    display_name: str
    legal_name: Optional[str]
    slug: str
    organization_type: str
    country_code: Optional[str]
    timezone: str
    default_currency: str
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    is_demo: bool = False


@dataclass(frozen=True)
class OrganizationMember:
    id: int
    organization_id: int
    user_id: int
    status: str
    joined_at: Optional[datetime]
    suspended_at: Optional[datetime]
    left_at: Optional[datetime]
    removed_at: Optional[datetime]
    created_by: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class OrganizationInvitation:
    id: int
    organization_id: int
    email_normalized: str
    token_hash: str
    status: str
    expires_at: datetime
    invited_by: int
    initial_role_code: str
    accepted_by: Optional[int]
    accepted_at: Optional[datetime]
    revoked_by: Optional[int]
    revoked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BusinessRole:
    id: int
    code: str
    display_name: str
    description: str
    scope: str
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Permission:
    id: int
    code: str
    description: str
    domain: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MemberRole:
    id: int
    member_id: int
    role_id: int
    status: str
    assigned_by: int
    assigned_at: datetime
    revoked_by: Optional[int]
    revoked_at: Optional[datetime]


@dataclass(frozen=True)
class UserOrganizationPreference:
    user_id: int
    active_organization_id: Optional[int]
    updated_at: datetime
    updated_by: Optional[int]


@dataclass(frozen=True)
class AuditLogEntry:
    id: int
    organization_id: Optional[int]
    actor_user_id: Optional[int]
    actor_platform_role: Optional[str]
    action: str
    target_type: str
    target_id: Optional[str]
    previous_values_json: Optional[str]
    new_values_json: Optional[str]
    reason: Optional[str]
    request_id: Optional[str]
    source: str
    result: str
    occurred_at: datetime


def row_to_dict(columns: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
    return {columns[i]: row[i] for i in range(len(columns))}
