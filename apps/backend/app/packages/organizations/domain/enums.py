"""Shared status enums for organizations persistence (Spec 016)."""

from __future__ import annotations

from enum import Enum


class OrganizationStatus(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED_BY_PLATFORM = "suspended_by_platform"
    CLOSED = "closed"


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LEFT = "left"
    REMOVED = "removed"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class MemberRoleStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


ORGANIZATION_STATUSES = frozenset(s.value for s in OrganizationStatus)
MEMBERSHIP_STATUSES = frozenset(s.value for s in MembershipStatus)
INVITATION_STATUSES = frozenset(s.value for s in InvitationStatus)
MEMBER_ROLE_STATUSES = frozenset(s.value for s in MemberRoleStatus)
