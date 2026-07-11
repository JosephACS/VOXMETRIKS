"""Conceptual domain events (no event bus)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class DomainEvent:
    name: str
    occurred_at: datetime
    organization_id: Optional[int] = None
    actor_user_id: Optional[int] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    payload: Optional[dict] = None


def evt(
    name: str,
    *,
    occurred_at: datetime,
    organization_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> DomainEvent:
    return DomainEvent(
        name=name,
        occurred_at=occurred_at,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
    )


# Named constants for audit / return payloads
ORGANIZATION_PROVISIONED = "OrganizationProvisioned"
ORGANIZATION_ACTIVATED = "OrganizationActivated"
ORGANIZATION_SUSPENDED = "OrganizationSuspended"
ORGANIZATION_REINSTATED = "OrganizationReinstated"
ORGANIZATION_CLOSED = "OrganizationClosed"
MEMBER_JOINED = "MemberJoined"
MEMBER_SUSPENDED = "MemberSuspended"
MEMBER_UNSUSPENDED = "MemberUnsuspended"
MEMBER_LEFT = "MemberLeft"
MEMBER_REMOVED = "MemberRemoved"
INVITATION_CREATED = "InvitationCreated"
INVITATION_ACCEPTED = "InvitationAccepted"
INVITATION_REVOKED = "InvitationRevoked"
INVITATION_RESENT = "InvitationResent"
MEMBER_ROLE_ASSIGNED = "MemberRoleAssigned"
MEMBER_ROLE_REVOKED = "MemberRoleRevoked"
ACTIVE_ORGANIZATION_CHANGED = "ActiveOrganizationChanged"
ACTIVE_ORGANIZATION_CLEARED = "ActiveOrganizationCleared"
