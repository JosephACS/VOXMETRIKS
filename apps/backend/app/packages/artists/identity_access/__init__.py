"""Spec 046 — Artist Space identity & access (membership-based).

Spec 051 adds catalog/release capabilities and the hidden backing tenant type.
"""

from __future__ import annotations

from app.packages.organizations.domain.enums import ARTIST_WORKSPACE_TYPE

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "owner": frozenset(
        {
            "artist_space.view",
            "artist_space.profile.update",
            "artist_space.team.manage",
            "artist_space.access.review",
            "artist_space.invite",
            "artist_space.catalog.view",
            "artist_space.release.create",
            "artist_space.release.edit",
            "artist_space.release.submit",
        }
    ),
    "administrator": frozenset(
        {
            "artist_space.view",
            "artist_space.profile.update",
            "artist_space.team.manage",
            "artist_space.access.review",
            "artist_space.invite",
            "artist_space.catalog.view",
            "artist_space.release.create",
            "artist_space.release.edit",
            "artist_space.release.submit",
        }
    ),
    "member": frozenset(
        {
            "artist_space.view",
            "artist_space.catalog.view",
            "artist_space.release.create",
            "artist_space.release.edit",
        }
    ),
    "reader": frozenset({"artist_space.view", "artist_space.catalog.view"}),
}

INVITE_ROLES = frozenset({"administrator", "member", "reader"})
ALL_ROLES = frozenset({"owner", "administrator", "member", "reader"})
REQUEST_TYPES = frozenset({"claim_ownership", "request_access", "create_new"})
RELATIONSHIP_TYPES = frozenset(
    {"artist_self", "manager", "label_representative", "collaborator"}
)

# Sentinel kept only so legacy rows can be detected and migrated onto a real
# hidden workspace organization. Never write it on new profiles.
INDEPENDENT_ORG_ID = 0

# app_organization.organization_type of the hidden tenant backing an Artist Space.
# Canonical definition lives in the Organizations domain; re-exported here so the
# artist identity layer reads naturally.
__all__ = [
    "ALL_ROLES",
    "ARTIST_WORKSPACE_TYPE",
    "INDEPENDENT_ORG_ID",
    "INVITE_ROLES",
    "RELATIONSHIP_TYPES",
    "REQUEST_TYPES",
    "ROLE_PERMISSIONS",
    "permissions_for_role",
    "role_has_permission",
]


def permissions_for_role(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role, frozenset()))


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
