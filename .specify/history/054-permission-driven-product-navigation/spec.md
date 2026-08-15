# Feature 054 — Permission-Driven Product Navigation

**Branch:** `codex/054-role-aware-product-navigation`
**Status:** Approved
**Product scope:** One navigation and module-visibility authority for every VOXMETRIKS workspace

## Problem

VOXMETRIKS currently has overlapping navigation policies: contextual space navigation, legacy shell navigation, module-context tabs, product-surface exceptions and username-based presentation behavior. A user can see a link that ends in 403, lose a module they are authorized to use, or receive different menus while session data is loading.

## Product decision

Navigation is permission-driven, not role-name-driven. Existing backend permissions, platform roles, artist capabilities, organization access tier and active space are authoritative. Role names may explain a persona in tests, but must not grant UI access by themselves.

No domain module is deleted in this feature. A module is visible only when it belongs to the active space, is available for the current tier and the user has its required capability. Valid deep links remain valid; hiding a link is not authorization.

## Functional requirements

### FR-001 — Single registry

One typed registry SHALL declare each product surface: stable id, label key, icon id, destination, active-space kinds, required capability, tier requirement, optional staff/platform constraint and module-context grouping.

### FR-002 — One decision pipeline

Sidebar items, bootstrap/predicted navigation, module-context tabs and route presentation SHALL consume the same pure access decision. No secondary array may re-enable or hide a surface independently.

### FR-003 — No identity-name exceptions

Usernames such as demo or presentation accounts SHALL NOT bypass module visibility or route access. Remove production decisions based on `presentationModeFromUser` and contradictory out-of-product allowlists.

### FR-004 — Space isolation

- Personal: listening, library, account and explicit entries to artist/organization journeys.
- Artist: artist profile, team, music and artist-scoped publishing allowed by artist capabilities.
- Organization: only organization-scoped modules allowed by tier and permissions.
- Data Ops: engineering and workpanel surfaces allowed by existing staff capabilities.
- Platform Admin: artist requests, catalog reviews, unresolved audio and actual platform operations; no organization-scoped commercial links without an active organization context.

### FR-005 — Permission parity

CRM, Customer Success, campaigns, business analytics, catalog, rights, subscriptions, billing, royalties, reports and compliance SHALL declare their existing backend permission contract. A visible destination must not predictably return 401/403 for the same hydrated session.

### FR-006 — Honest reports access

An organization member with `report.view` SHALL see Reports even when not staff. Staff-only Workpanel remains staff/capability constrained.

### FR-007 — No navigation flash

Predicted or loading navigation SHALL pass through the same filter or render a stable loading shell. Unauthorized links must never flash before session/space hydration completes.

### FR-008 — Module tabs

Catalog, billing, reporting, Platform Ops and other contextual tab groups SHALL filter individual tabs with the same registry. Tabs cannot expose review, mutation or administration pages without their capability.

### FR-009 — Route behavior

Direct navigation to an unavailable module SHALL use the existing access-denied/module-unavailable behavior without leaking tenant data. This feature does not replace backend authorization.

### FR-010 — Responsive and accessible navigation

Desktop and mobile navigation SHALL preserve focus order, keyboard activation, current-page state, accessible labels and drawer behavior. No forced E2E interactions are accepted.

### FR-011 — Editable product data remains reachable

Authorized users SHALL retain discoverable paths to edit organization settings, members, invitations, artist profile/team and subscription/billing information. Consolidation must not make implemented edit flows deep-link-only.

## Non-goals

- Rewriting backend RBAC or role bundles.
- Deleting CRM, Customer Success, compliance, royalties, ROI or other domain packages.
- Adding a new authorization service or database table.
- Redesigning dashboards or implementing new business workflows.
- Treating simulated payments, payouts or ROI as real transactions.

## Acceptance criteria

1. One registry and one pure access decision serve sidebar and contextual tabs.
2. No username-based presentation bypass remains in production access decisions.
3. Every registered organization module declares tier and permission requirements.
4. Owner, billing, analyst, viewer, artist, engineer and platform-admin persona tests receive distinct valid surfaces.
5. Visible-link parity tests show no predictable 403 for hydrated personas.
6. Platform Admin sees real platform operations and no contextless organization links.
7. Desktop and mobile E2E use normal pointer/touch/keyboard interactions with zero skips and an isolated temporary DB.
8. Canonical DuckDB fingerprint is unchanged.
