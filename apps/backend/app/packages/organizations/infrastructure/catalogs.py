"""System role / permission catalog definitions (Spec 016 I1).

Matrix aligned with role-and-permission-model.md for non-FUTURE permissions.
invitation.* and organization.create are seeded for 016 scope (user I1 auth);
organization.create has no org-role mapping (pre-org authenticated action).
FUTURE permissions (billing.view, artist.view, campaign.view) are NOT seeded.
"""

from __future__ import annotations

from typing import Final

# (code, display_name, description)
BUSINESS_ROLES: Final[tuple[tuple[str, str, str], ...]] = (
    ("owner", "Owner", "Full organizational control including close"),
    ("administrator", "Administrator", "Operational administration without close"),
    ("billing_manager", "Billing Manager", "Future billing access; limited org view in v1"),
    ("finance", "Finance", "Financial reporting and audit view"),
    ("artist_manager", "Artist Manager", "Artist-domain prep; member and analytics view"),
    ("marketing_manager", "Marketing Manager", "Campaign prep; member and analytics view"),
    ("analyst", "Analyst", "Analytics and reports; read-only membership"),
    ("artist", "Artist", "Limited artist self-scope when domain exists"),
    ("viewer", "Viewer", "Read-only organization and analytics"),
)

# (code, description, domain)
PERMISSIONS: Final[tuple[tuple[str, str, str], ...]] = (
    ("organization.view", "View organization profile", "organization"),
    ("organization.create", "Create a new organization (pre-membership)", "organization"),
    ("organization.update", "Update organization profile", "organization"),
    ("organization.close", "Close organization", "organization"),
    ("member.view", "View organization members", "member"),
    ("member.invite", "Invite members", "member"),
    ("member.suspend", "Suspend members", "member"),
    ("member.remove", "Remove members", "member"),
    ("role.view", "View member roles", "role"),
    ("role.assign", "Assign or revoke member roles", "role"),
    ("invitation.view", "View invitations", "invitation"),
    ("invitation.revoke", "Revoke invitations", "invitation"),
    ("audit.view", "View organization audit log", "audit"),
    ("analytics.view", "View organization analytics", "analytics"),
    ("report.view", "View organization reports", "report"),
)

# role_code -> frozenset(permission_code)
ROLE_PERMISSION_MATRIX: Final[dict[str, frozenset[str]]] = {
    "owner": frozenset(
        {
            "organization.view",
            "organization.update",
            "organization.close",
            "member.view",
            "member.invite",
            "member.suspend",
            "member.remove",
            "role.view",
            "role.assign",
            "invitation.view",
            "invitation.revoke",
            "audit.view",
            "analytics.view",
            "report.view",
        }
    ),
    "administrator": frozenset(
        {
            "organization.view",
            "organization.update",
            "member.view",
            "member.invite",
            "member.suspend",
            "member.remove",
            "role.view",
            "role.assign",
            "invitation.view",
            "invitation.revoke",
            "audit.view",
            "analytics.view",
            "report.view",
        }
    ),
    "billing_manager": frozenset(
        {
            "organization.view",
            "member.view",
        }
    ),
    "finance": frozenset(
        {
            "organization.view",
            "member.view",
            "audit.view",
            "report.view",
        }
    ),
    "artist_manager": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
        }
    ),
    "marketing_manager": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            "report.view",
        }
    ),
    "analyst": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            "report.view",
        }
    ),
    "artist": frozenset(
        {
            "organization.view",
        }
    ),
    "viewer": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
        }
    ),
}

ORGANIZATION_SCOPE: Final[str] = "organization"
