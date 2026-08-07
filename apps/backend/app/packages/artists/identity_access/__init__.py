"""Spec 046 — Artist Space identity & access (membership-based)."""

from __future__ import annotations

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "owner": frozenset(
        {
            "artist_space.view",
            "artist_space.profile.update",
            "artist_space.team.manage",
            "artist_space.access.review",
            "artist_space.invite",
        }
    ),
    "administrator": frozenset(
        {
            "artist_space.view",
            "artist_space.profile.update",
            "artist_space.team.manage",
            "artist_space.access.review",
            "artist_space.invite",
        }
    ),
    "member": frozenset({"artist_space.view"}),
    "reader": frozenset({"artist_space.view"}),
}

INVITE_ROLES = frozenset({"administrator", "member", "reader"})
ALL_ROLES = frozenset({"owner", "administrator", "member", "reader"})
REQUEST_TYPES = frozenset({"claim_ownership", "request_access", "create_new"})
INDEPENDENT_ORG_ID = 0


def permissions_for_role(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role, frozenset()))


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
