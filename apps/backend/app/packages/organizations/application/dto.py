"""Internal DTOs and actor context (not HTTP schemas)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.packages.organizations.domain.entities import (
    Organization,
    OrganizationInvitation,
    OrganizationMember,
    UserOrganizationPreference,
)
from app.packages.organizations.domain.events import DomainEvent


@dataclass(frozen=True)
class ActorContext:
    """Authenticated actor for domain use cases (wired by I3 later)."""

    user_id: int
    platform_role: Optional[str] = None
    request_id: Optional[str] = None

    @property
    def is_platform_operator(self) -> bool:
        """Elevated platform ops (suspend/reinstate) — deny-by-default.

        Technical identity roles ``admin`` / ``engineer`` / ``user`` are NOT
        platform operators. Explicit ``platform_admin`` / ``security_admin``
        only. Full elevated-access grants (reason, expiry, audit) are deferred
        to a future stage — no temporary bypass via technical admin.
        """
        role = (self.platform_role or "").lower()
        return role in {"platform_admin", "security_admin"}


@dataclass(frozen=True)
class CreateOrganizationCommand:
    actor: ActorContext
    display_name: str
    slug: str
    organization_type: str
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    default_currency: Optional[str] = None
    legal_name: Optional[str] = None
    make_active: bool = True
    # Documented debt: no persistent idempotency_key column in I1 schema.
    idempotency_key: Optional[str] = None
    client_intent_id: Optional[str] = None
    slug_explicit: bool = False


@dataclass(frozen=True)
class CreateOrganizationResult:
    organization: Organization
    membership: OrganizationMember
    events: list[DomainEvent] = field(default_factory=list)
    reused_existing: bool = False
    idempotency_mode: str = "slug_deterministic"


@dataclass(frozen=True)
class InvitationCreateResult:
    invitation: OrganizationInvitation
    invite_token: str
    returned_once: bool
    email_delivery_status: str
    events: list[DomainEvent] = field(default_factory=list)


@dataclass(frozen=True)
class AcceptInvitationResult:
    organization: Organization
    membership: OrganizationMember
    events: list[DomainEvent] = field(default_factory=list)


@dataclass(frozen=True)
class PreferenceResult:
    preference: UserOrganizationPreference
    events: list[DomainEvent] = field(default_factory=list)


@dataclass(frozen=True)
class MutationResult:
    data: Any
    events: list[DomainEvent] = field(default_factory=list)
