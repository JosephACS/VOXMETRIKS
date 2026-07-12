"""Platform RBAC catalog definitions — Spec 017 / 018.

Roles: sales_agent, sales_manager, platform_admin, auditor.
Scope: platform (not org-scoped).
Do NOT map user/admin/engineer identity roles to commercial roles.
Spec 018 adds: plan.*, plan_price.*, plan_feature.*, addon.* permissions.
Spec 026 adds: audit.search platform-scoped permission.
Spec 027 adds: ops.view, ops.manage, ops.webhooks, ops.flags platform permissions.
"""

from __future__ import annotations

from typing import Final

# (code, display_name, description)
PLATFORM_ROLES: Final[tuple[tuple[str, str, str], ...]] = (
    ("sales_agent", "Sales Agent", "Prospects, opportunities, activities, quotations, conversion"),
    ("sales_manager", "Sales Manager", "Full agent capabilities plus approvals, audit view"),
    ("platform_admin", "Platform Admin", "Break-glass / configuration; full CRM access"),
    ("auditor", "Auditor", "Read-only audit view for CRM"),
)

# (code, description, domain)
PLATFORM_PERMISSIONS: Final[tuple[tuple[str, str, str], ...]] = (
    ("crm.prospect.view", "View prospects", "crm"),
    ("crm.prospect.create", "Create prospects", "crm"),
    ("crm.prospect.update", "Update prospects and non-convert transitions", "crm"),
    ("crm.opportunity.view", "View opportunity pipeline", "crm"),
    ("crm.opportunity.create", "Create opportunities", "crm"),
    ("crm.opportunity.update", "Advance opportunity stages", "crm"),
    ("crm.opportunity.close", "Close opportunities (won/lost/canceled)", "crm"),
    ("crm.activity.manage", "CRUD sales activities", "crm"),
    ("quotation.create", "Create draft quotation/version", "quotation"),
    ("quotation.update", "Edit draft quotation", "quotation"),
    ("quotation.send", "Send quotation to prospect", "quotation"),
    ("quotation.approve", "Approve quotation/discount (manager)", "quotation"),
    ("contract.create", "Create commercial contract", "contract"),
    ("contract.approve", "Approve contract", "contract"),
    ("contract.accept", "Register academic contract acceptance", "contract"),
    ("customer.convert", "Execute customer conversion", "crm"),
    ("crm.audit.view", "View CRM audit log", "crm"),
    # Spec 018 — plan catalog management
    ("plan.view", "View plan catalog", "subscription"),
    ("plan.create", "Create and update plans", "subscription"),
    ("plan.activate", "Activate / publish a plan", "subscription"),
    ("plan.archive", "Archive a plan", "subscription"),
    ("plan_price.manage", "Manage plan prices", "subscription"),
    ("plan_feature.manage", "Manage plan features", "subscription"),
    ("addon.manage", "Manage addons catalog", "subscription"),
    # Spec 026 — global audit search (platform-scoped)
    ("audit.search", "Search global audit log across organizations", "compliance"),
    # Spec 027 — platform operations
    ("ops.view", "View platform operations: health, jobs, notifications, backups", "ops"),
    ("ops.manage", "Manage platform jobs, incidents, backups, provider config", "ops"),
    ("ops.webhooks", "Manage webhook receivers and deliveries", "ops"),
    ("ops.flags", "Manage feature flags and config registry", "ops"),
)

# role_code -> frozenset(permission_code)
PLATFORM_ROLE_PERMISSION_MATRIX: Final[dict[str, frozenset[str]]] = {
    "sales_agent": frozenset({
        "crm.prospect.view",
        "crm.prospect.create",
        "crm.prospect.update",
        "crm.opportunity.view",
        "crm.opportunity.create",
        "crm.opportunity.update",
        "crm.opportunity.close",
        "crm.activity.manage",
        "quotation.create",
        "quotation.update",
        "quotation.send",
        "contract.create",
        "contract.accept",
        "customer.convert",
    }),
    "sales_manager": frozenset({
        "crm.prospect.view",
        "crm.prospect.create",
        "crm.prospect.update",
        "crm.opportunity.view",
        "crm.opportunity.create",
        "crm.opportunity.update",
        "crm.opportunity.close",
        "crm.activity.manage",
        "quotation.create",
        "quotation.update",
        "quotation.send",
        "quotation.approve",
        "contract.create",
        "contract.approve",
        "contract.accept",
        "customer.convert",
        "crm.audit.view",
    }),
    "platform_admin": frozenset({
        "crm.prospect.view",
        "crm.prospect.create",
        "crm.prospect.update",
        "crm.opportunity.view",
        "crm.opportunity.create",
        "crm.opportunity.update",
        "crm.opportunity.close",
        "crm.activity.manage",
        "quotation.create",
        "quotation.update",
        "quotation.send",
        "quotation.approve",
        "contract.create",
        "contract.approve",
        "contract.accept",
        "customer.convert",
        "crm.audit.view",
        # Spec 018 — plan catalog management
        "plan.view",
        "plan.create",
        "plan.activate",
        "plan.archive",
        "plan_price.manage",
        "plan_feature.manage",
        "addon.manage",
        # Spec 026 / 027
        "audit.search",
        "ops.view",
        "ops.manage",
        "ops.webhooks",
        "ops.flags",
    }),
    "auditor": frozenset({
        "crm.prospect.view",
        "crm.opportunity.view",
        "crm.audit.view",
        "plan.view",
        "audit.search",
        "ops.view",
    }),
}
