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
Spec 024 adds: report.generate/approve/publish/export, decision.* (Executive Reporting).
Spec 025 adds: customer_success.*, customer_health.*, support.*, and CS/support roles.
Spec 030 adds: royalty.* org-scoped permissions (pools, settlements, simulated payouts).
Spec 031 adds: publishing.* org-scoped permissions + catalog_reviewer role.
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
    ("auditor", "Auditor", "Read-only audit and reporting access"),
    ("customer_success_manager", "Customer Success Manager", "CS onboarding, health, risk, renewal"),
    ("support_agent", "Support Agent", "Support case handling within organization"),
    ("catalog_reviewer", "Catalog Reviewer", "Review and publish artist release submissions"),
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
    # Spec 024 — executive reporting & business decisions
    ("report.generate", "Create report definitions and generate snapshots", "report"),
    ("report.approve", "Approve executive reports", "report"),
    ("report.publish", "Publish or archive executive reports", "report"),
    ("report.export", "Export executive reports (CSV)", "report"),
    ("decision.view", "View business decisions and follow-ups", "decision"),
    ("decision.create", "Record business decisions", "decision"),
    ("decision.approve", "Approve business decisions", "decision"),
    ("decision.update", "Update decision actions and follow-ups", "decision"),
    ("decision.complete", "Complete business decisions", "decision"),
    # Spec 025 — customer success & support
    ("customer_success.view", "View CS onboarding and dashboard", "customer_success"),
    ("customer_success.manage", "Manage CS onboarding steps", "customer_success"),
    ("customer_health.view", "View customer health snapshots", "customer_success"),
    ("customer_health.calculate", "Calculate customer health scores", "customer_success"),
    ("customer_risk.manage", "Create and update customer risks", "customer_success"),
    ("customer_intervention.manage", "Assign and complete interventions", "customer_success"),
    ("renewal_readiness.view", "View renewal readiness evaluations", "customer_success"),
    ("expansion.manage", "Create expansion opportunities", "customer_success"),
    ("support.view", "View support cases", "support"),
    ("support.create", "Create support cases", "support"),
    ("support.assign", "Assign support cases", "support"),
    ("support.respond", "Add customer-visible support messages", "support"),
    ("support.internal_note", "Add internal support notes", "support"),
    ("support.escalate", "Escalate support cases", "support"),
    ("support.resolve", "Resolve support cases", "support"),
    ("support.close", "Close or reopen support cases", "support"),
    ("support.audit.view", "View support audit and SLA events", "support"),
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
    # Spec 030 — royalties, settlements, simulated payouts
    ("royalty.view", "View royalty pools, settlements, statements, and metrics", "royalty"),
    ("royalty.pool.manage", "Create pools and add B2C/manual B2B revenue sources", "royalty"),
    ("royalty.settle", "Run pro-rata settlement, contract splits, and statements", "royalty"),
    ("royalty.adjust", "Apply settlement adjustments", "royalty"),
    ("royalty.payout", "Create and simulate payout batches (no real money)", "royalty"),
    ("royalty.approve", "Approve pools and settlements", "royalty"),
    # Spec 031 — artist submission / catalog review / publish
    ("publishing.view", "View release submissions and publication history", "publishing"),
    ("publishing.create", "Create drafts, upload media, edit submission metadata", "publishing"),
    ("publishing.submit", "Submit releases for catalog review", "publishing"),
    ("publishing.review", "Approve, reject, or request changes on submissions", "publishing"),
    ("publishing.publish", "Schedule and publish approved releases", "publishing"),
    ("publishing.takedown", "Suspend or withdraw published releases", "publishing"),
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
            "report.generate",
            "report.approve",
            "report.publish",
            "report.export",
            "decision.view",
            "decision.create",
            "decision.approve",
            "decision.update",
            "decision.complete",
            "customer_success.view",
            "customer_success.manage",
            "customer_health.view",
            "customer_health.calculate",
            "customer_risk.manage",
            "customer_intervention.manage",
            "renewal_readiness.view",
            "expansion.manage",
            "support.view",
            "support.create",
            "support.assign",
            "support.respond",
            "support.internal_note",
            "support.escalate",
            "support.resolve",
            "support.close",
            "support.audit.view",
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
            # Spec 030
            "royalty.view",
            "royalty.pool.manage",
            "royalty.settle",
            "royalty.adjust",
            "royalty.payout",
            "royalty.approve",
            # Spec 031
            "publishing.view",
            "publishing.create",
            "publishing.submit",
            "publishing.review",
            "publishing.publish",
            "publishing.takedown",
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
            "report.generate",
            "report.approve",
            "report.publish",
            "report.export",
            "decision.view",
            "decision.create",
            "decision.approve",
            "decision.update",
            "decision.complete",
            "customer_success.view",
            "customer_success.manage",
            "customer_health.view",
            "customer_health.calculate",
            "customer_risk.manage",
            "customer_intervention.manage",
            "renewal_readiness.view",
            "expansion.manage",
            "support.view",
            "support.create",
            "support.assign",
            "support.respond",
            "support.internal_note",
            "support.escalate",
            "support.resolve",
            "support.close",
            "support.audit.view",
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
            # Spec 030
            "royalty.view",
            "royalty.pool.manage",
            "royalty.settle",
            "royalty.adjust",
            "royalty.payout",
            "royalty.approve",
            # Spec 031
            "publishing.view",
            "publishing.create",
            "publishing.submit",
            "publishing.review",
            "publishing.publish",
            "publishing.takedown",
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
            # Spec 030 — finance ops without inventing platform_admin money power
            "royalty.view",
            "royalty.pool.manage",
            "royalty.settle",
            "royalty.adjust",
            "royalty.payout",
            "royalty.approve",
        }
    ),
    "finance": frozenset(
        {
            "organization.view",
            "member.view",
            "audit.view",
            "report.view",
            "report.export",
            "decision.view",
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
            # Spec 030
            "royalty.view",
            "royalty.pool.manage",
            "royalty.settle",
            "royalty.adjust",
            "royalty.payout",
            "royalty.approve",
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
            # Spec 030 — view-only
            "royalty.view",
            # Spec 031 — create/submit only
            "publishing.view",
            "publishing.create",
            "publishing.submit",
        }
    ),
    "marketing_manager": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            "report.view",
            "report.generate",
            "report.export",
            "decision.view",
            "decision.create",
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
            "report.generate",
            "report.export",
            "decision.view",
            "decision.create",
            "decision.update",
            # Spec 022
            "campaign.view",
            # Spec 023
            "biz_analytics.view",
            "biz_analytics.manage",
            "customer_success.view",
            "customer_health.view",
            "renewal_readiness.view",
            "support.view",
        }
    ),
    "artist": frozenset(
        {
            "organization.view",
            # Spec 020
            "artist.view",
            # Spec 026
            "privacy.request",
            "support.create",
            "support.view",
            # Spec 031
            "publishing.view",
            "publishing.create",
            "publishing.submit",
        }
    ),
    "catalog_reviewer": frozenset(
        {
            "organization.view",
            "member.view",
            "artist.view",
            "rights.view",
            "publishing.view",
            "publishing.review",
            "publishing.publish",
            "publishing.takedown",
        }
    ),
    "viewer": frozenset(
        {
            "organization.view",
            "member.view",
            "analytics.view",
            "report.view",
            "decision.view",
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
            "customer_success.view",
            "customer_health.view",
            "renewal_readiness.view",
            "support.view",
            "support.create",
        }
    ),
    "auditor": frozenset(
        {
            "organization.view",
            "member.view",
            "audit.view",
            "report.view",
            "decision.view",
            "biz_analytics.view",
            "compliance.view",
            "audit.search",
            "customer_success.view",
            "customer_health.view",
            "renewal_readiness.view",
            "support.view",
            "support.audit.view",
        }
    ),
    "customer_success_manager": frozenset(
        {
            "organization.view",
            "member.view",
            "customer_success.view",
            "customer_success.manage",
            "customer_health.view",
            "customer_health.calculate",
            "customer_risk.manage",
            "customer_intervention.manage",
            "renewal_readiness.view",
            "expansion.manage",
            "support.view",
            "support.create",
            "support.assign",
            "support.respond",
            "support.internal_note",
            "support.escalate",
            "subscription.view",
            "report.view",
            "decision.view",
        }
    ),
    "support_agent": frozenset(
        {
            "organization.view",
            "member.view",
            "support.view",
            "support.create",
            "support.assign",
            "support.respond",
            "support.internal_note",
            "support.escalate",
            "support.resolve",
            "support.close",
            "support.audit.view",
            "customer_success.view",
            "customer_health.view",
        }
    ),
}

ORGANIZATION_SCOPE: Final[str] = "organization"
