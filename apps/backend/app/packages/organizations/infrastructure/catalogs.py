"""System role / permission catalog definitions (Spec 016 I1 / 018 / 020).

Matrix aligned with role-and-permission-model.md for non-FUTURE permissions.
invitation.* and organization.create are seeded for 016 scope (user I1 auth);
organization.create has no org-role mapping (pre-org authenticated action).
Spec 018 adds: subscription.*, usage.* org-scoped permissions.
Spec 019 adds: billing.*, invoice.*, payment.*, refund.manage, credit_note.manage.
Spec 020 adds: artist.* org-scoped permissions (Artists and Team Management).
Spec 021 adds: rights.* org-scoped permissions (Catalog Rights and Contracts).
Spec 022 adds: campaign.* org-scoped permissions (Campaigns, Budgets and ROI).
Spec 023 adds: biz_analytics.* org-scoped permissions (Engagement and Business Analytics).
Spec 026 adds: compliance.*, privacy.*, incident.manage, audit.search org-scoped permissions.
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
    # Spec 018 — subscription permissions (org-scoped)
    ("subscription.view", "View organization subscriptions and entitlements", "subscription"),
    ("subscription.create", "Start subscription or trial", "subscription"),
    ("subscription.change", "Change plan, activate, or manage addons", "subscription"),
    ("subscription.cancel", "Cancel subscription", "subscription"),
    ("subscription.reactivate", "Reactivate a canceled/expired subscription", "subscription"),
    ("usage.view", "View and record usage", "subscription"),
    # Spec 019 — billing permissions (org-scoped)
    ("billing.view", "View billing profile, invoices, payments, ledger", "billing"),
    ("billing.manage", "Create/update billing profile, void invoices, record transfers", "billing"),
    ("invoice.view", "View invoices and items", "billing"),
    ("invoice.create", "Create and issue invoices", "billing"),
    ("invoice.void", "Void invoices", "billing"),
    ("payment.view", "View payments and attempts", "billing"),
    ("payment.manage", "Initiate, confirm, reconcile payments", "billing"),
    ("refund.manage", "Process refunds", "billing"),
    ("credit_note.manage", "Create and apply credit notes", "billing"),
    # Spec 020 — artists and team management permissions (org-scoped)
    ("artist.view", "View artist profiles, team, and history", "artist"),
    ("artist.create", "Create new artist profiles", "artist"),
    ("artist.update", "Update artist profile, org links, external identifiers", "artist"),
    ("artist.assign", "Assign managers and manage team members", "artist"),
    ("artist.archive", "Archive artist profiles", "artist"),
    ("artist.transfer", "Transfer artist primary organization ownership", "artist"),
    # Spec 021 — catalog rights and contracts permissions (org-scoped)
    ("rights.view", "View catalog assets, rights contracts, coverage, and history", "rights"),
    ("rights.create", "Register assets/releases and create rights contracts, parties, territories", "rights"),
    ("rights.update", "Update rights contracts, link warehouse tracks, submit for approval", "rights"),
    ("rights.approve", "Approve or reject rights contracts", "rights"),
    ("rights.conflict", "Open, detect, and resolve rights conflicts", "rights"),
    ("rights.archive", "Archive rights contracts", "rights"),
    # Spec 022 — campaigns permissions (org-scoped)
    ("campaign.view", "View campaigns, budgets, expenses, and ROI", "campaign"),
    ("campaign.create", "Create new campaigns", "campaign"),
    ("campaign.update", "Update campaigns, objectives, targets, and results", "campaign"),
    ("campaign.approve", "Approve campaigns, attribution, and revenue", "campaign"),
    ("campaign.expense", "Record campaign expenses", "campaign"),
    ("campaign.close", "Complete or close campaigns", "campaign"),
    # Spec 023 — business analytics permissions (org-scoped)
    ("biz_analytics.view", "View enterprise analytics dashboard, KPIs, and recommendations", "biz_analytics"),
    ("biz_analytics.manage", "Manage KPI snapshots and data quality checks", "biz_analytics"),
    ("biz_analytics.alert", "Create and acknowledge business alerts", "biz_analytics"),
    # Spec 026 — compliance and privacy permissions (org-scoped)
    ("compliance.view", "View compliance terms, consent, DSR, retention, and incidents", "compliance"),
    ("compliance.manage", "Manage terms, consent definitions, retention, and legal holds", "compliance"),
    ("privacy.request", "Submit data subject requests (access/export/correction/deletion)", "compliance"),
    ("privacy.export", "Process and export data subject request data", "compliance"),
    ("incident.manage", "Manage security incidents and response actions", "compliance"),
    ("audit.search", "Search organization audit log with filters", "compliance"),
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
            # Spec 018
            "subscription.view",
            "subscription.create",
            "subscription.change",
            "subscription.cancel",
            "subscription.reactivate",
            "usage.view",
            # Spec 019
            "billing.view",
            "billing.manage",
            "invoice.view",
            "invoice.create",
            "invoice.void",
            "payment.view",
            "payment.manage",
            "refund.manage",
            "credit_note.manage",
            # Spec 020
            "artist.view",
            "artist.create",
            "artist.update",
            "artist.assign",
            "artist.archive",
            "artist.transfer",
            # Spec 021
            "rights.view",
            "rights.create",
            "rights.update",
            "rights.approve",
            "rights.conflict",
            "rights.archive",
            # Spec 022
            "campaign.view",
            "campaign.create",
            "campaign.update",
            "campaign.approve",
            "campaign.expense",
            "campaign.close",
            # Spec 023
            "biz_analytics.view",
            "biz_analytics.manage",
            "biz_analytics.alert",
            # Spec 026
            "compliance.view",
            "compliance.manage",
            "privacy.request",
            "privacy.export",
            "incident.manage",
            "audit.search",
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
            # Spec 018
            "subscription.view",
            "subscription.change",
            "usage.view",
            # Spec 019
            "billing.view",
            "invoice.view",
            "payment.view",
            # Spec 020
            "artist.view",
            "artist.create",
            "artist.update",
            "artist.assign",
            "artist.archive",
            # Spec 021
            "rights.view",
            "rights.create",
            "rights.update",
            "rights.approve",
            "rights.conflict",
            "rights.archive",
            # Spec 022
            "campaign.view",
            "campaign.create",
            "campaign.update",
            "campaign.approve",
            "campaign.expense",
            "campaign.close",
            # Spec 023
            "biz_analytics.view",
            "biz_analytics.manage",
            "biz_analytics.alert",
            # Spec 026
            "compliance.view",
            "compliance.manage",
            "privacy.request",
            "privacy.export",
            "incident.manage",
            "audit.search",
        }
    ),
    "billing_manager": frozenset(
        {
            "organization.view",
            "member.view",
            # Spec 018
            "subscription.view",
            "subscription.create",
            "subscription.change",
            "subscription.cancel",
            "subscription.reactivate",
            "usage.view",
            # Spec 019
            "billing.view",
            "billing.manage",
            "invoice.view",
            "invoice.create",
            "invoice.void",
            "payment.view",
            "payment.manage",
            "refund.manage",
            "credit_note.manage",
        }
    ),
    "finance": frozenset(
        {
            "organization.view",
            "member.view",
            "audit.view",
            "report.view",
            # Spec 019
            "billing.view",
            "invoice.view",
            "payment.view",
            # Spec 021
            "rights.view",
            # Spec 022
            "campaign.view",
            "campaign.approve",
            # Spec 023
            "biz_analytics.view",
            # Spec 026
            "compliance.view",
            "audit.search",
        }
    ),
    "artist_manager": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            # Spec 020
            "artist.view",
            "artist.create",
            "artist.update",
            "artist.assign",
            # Spec 021
            "rights.view",
            "rights.create",
            "rights.update",
        }
    ),
    "marketing_manager": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            "report.view",
            # Spec 022
            "campaign.view",
            "campaign.create",
            "campaign.update",
            "campaign.expense",
            # Spec 023
            "biz_analytics.view",
            # Spec 026
            "privacy.request",
        }
    ),
    "analyst": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            "report.view",
            # Spec 022
            "campaign.view",
            # Spec 023
            "biz_analytics.view",
            "biz_analytics.manage",
        }
    ),
    "artist": frozenset(
        {
            "organization.view",
            # Spec 020
            "artist.view",
            # Spec 026
            "privacy.request",
        }
    ),
    "viewer": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            # Spec 020
            "artist.view",
            # Spec 021
            "rights.view",
            # Spec 022
            "campaign.view",
            # Spec 023
            "biz_analytics.view",
            # Spec 026
            "compliance.view",
            "privacy.request",
        }
    ),
}

ORGANIZATION_SCOPE: Final[str] = "organization"
