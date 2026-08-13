"""Pure domain rules: normalization, transitions, last-owner predicates."""

from __future__ import annotations

import re
from typing import Optional

from app.core.email_format import is_valid_email_format
from app.packages.organizations.domain.enums import (
    InvitationStatus,
    MembershipStatus,
    OrganizationStatus,
)
from app.packages.organizations.domain.errors import (
    InvalidOrganizationTransition,
    ValidationError,
)

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PLATFORM_ROLE_CODES = frozenset(
    {
        "user",
        "admin",
        "engineer",
        "platform_admin",
        "security_admin",
        "sales_agent",
        "sales_manager",
        "customer_success_manager",
        "support_agent",
        "platform_finance",
        "auditor",
    }
)

# Organization transitions approved in lifecycle-state-machines.md (excl. reopen deferred)
ORG_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (OrganizationStatus.PROVISIONING.value, OrganizationStatus.ACTIVE.value),
        (OrganizationStatus.ACTIVE.value, OrganizationStatus.SUSPENDED_BY_PLATFORM.value),
        (OrganizationStatus.SUSPENDED_BY_PLATFORM.value, OrganizationStatus.ACTIVE.value),
        (OrganizationStatus.ACTIVE.value, OrganizationStatus.CLOSED.value),
        (
            OrganizationStatus.SUSPENDED_BY_PLATFORM.value,
            OrganizationStatus.CLOSED.value,
        ),
    }
)

MEMBER_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (MembershipStatus.ACTIVE.value, MembershipStatus.SUSPENDED.value),
        (MembershipStatus.SUSPENDED.value, MembershipStatus.ACTIVE.value),
        (MembershipStatus.ACTIVE.value, MembershipStatus.LEFT.value),
        (MembershipStatus.ACTIVE.value, MembershipStatus.REMOVED.value),
        (MembershipStatus.SUSPENDED.value, MembershipStatus.REMOVED.value),
    }
)

INVITE_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (InvitationStatus.PENDING.value, InvitationStatus.ACCEPTED.value),
        (InvitationStatus.PENDING.value, InvitationStatus.EXPIRED.value),
        (InvitationStatus.PENDING.value, InvitationStatus.REVOKED.value),
    }
)

DEFAULT_INVITE_TTL_DAYS = 7
MAX_INVITE_TTL_DAYS = 30


def normalize_slug(raw: str) -> str:
    value = (raw or "").strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value or not _SLUG_RE.match(value):
        raise ValidationError(f"Invalid organization slug: {raw!r}")
    if len(value) > 64:
        raise ValidationError("slug exceeds 64 characters")
    return value


def normalize_email(raw: str) -> str:
    value = (raw or "").strip().lower()
    if not is_valid_email_format(value):
        raise ValidationError("Invalid email format")
    return value


def is_platform_role_code(code: str) -> bool:
    return code.strip().lower() in _PLATFORM_ROLE_CODES


def assert_org_transition(current: str, target: str) -> None:
    if (current, target) not in ORG_TRANSITIONS:
        raise InvalidOrganizationTransition(
            f"Invalid organization transition {current} → {target}"
        )


def assert_member_transition(current: str, target: str) -> None:
    if (current, target) not in MEMBER_TRANSITIONS:
        raise ValidationError(
            f"Invalid membership transition {current} → {target}"
        )


def assert_invite_transition(current: str, target: str) -> None:
    if (current, target) not in INVITE_TRANSITIONS:
        raise ValidationError(
            f"Invalid invitation transition {current} → {target}"
        )


def organization_allows_member_mutations(status: str) -> bool:
    return status == OrganizationStatus.ACTIVE.value


def organization_allows_profile_update(status: str) -> bool:
    return status == OrganizationStatus.ACTIVE.value


def would_remove_last_active_owner(
    *,
    active_owner_count: int,
    target_is_active_owner: bool,
) -> bool:
    """True when the planned mutation would leave zero active owners."""
    if not target_is_active_owner:
        return False
    return active_owner_count <= 1
