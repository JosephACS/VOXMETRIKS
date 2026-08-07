# Spec 045 — FE dependency closure (self-contained branch)

## Purpose

Make `feature/045-spaces-contextual-navigation` buildable from a clean checkout of HEAD by committing Spec 043/044 frontend files that are already imported by tracked entrypoints, plus org/commercial route-guard alignment.

## Method (Step A)

Entrypoints walked (relative imports under `apps/frontend/src` only):

- `apps/frontend/src/app/app.routes.ts`
- `apps/frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.ts`
- `apps/frontend/src/app/core/spaces/space-context.service.ts`
- `apps/frontend/src/app/core/guards/product-surface.guard.ts`
- `apps/frontend/src/app/core/guards/with-product-surface-guard.ts`

Plus manual ensure-list for staff/nav/org-access, profiles layout, module-context*, activity, reports packages, platform-admin, unresolved-audio, catalog-hub.

`git ls-files --error-unmatch` classified each resolved `.ts/.html/.css` as tracked vs untracked. Tracked "dirty" filtered with `git diff --ignore-cr-at-eol` (spaces/product-surface working-tree noise was **CRLF/index only** — hashes matched HEAD → **not staged**).

## Decision A — UNTRACKED_REQUIRED (commit)

Production + tests required by HEAD imports / route loaders:

| Area | Paths |
|------|--------|
| Guards / nav | `platform-admin.guard.ts`, `staff-capability.guard.ts`, `nav-access.policy.ts` (+spec) |
| Layouts | `profiles-layout.component.ts`, `shell-layout.tokens.ts`, `dashboard-layout.sidebar-scroll.spec.ts` |
| Org access | `organization-access.ts` (+spec), `org-hub.page.ts`, `business-for-enterprises.page.ts` |
| Reports | `simple-reports/**`, `workpanel/**`, `complex-reports/**`, `reports-hub.page.ts`, `related-reports-panel.component.ts`, `report-presentation.ts`, `display-label.util.ts` |
| Catalog / platform | `catalog-hub.page.ts`, `unresolved-audio.page.ts` |
| Personal / activity | profile-selector (+css/spec), profile-switch, security-api, trusted-device, activity page+html+css, listening-activity.service |
| Module chrome | `module-context.ts` (+spec), `module-context-chrome.component.ts`, `module-unavailable.page.ts` |

## Decision B — TRACKED_MODIFIED (commit, scoped)

Include **route/guard/org context** content changes only (not entire dirty FE tree):

- Commercial/org routes: billing, campaigns, royalties, catalog-publishing, catalog-rights, subscriptions, organizations, artists, reporting, platform-ops
- `organization.guards.ts`, `organization-context.service.ts`, `organization.models.ts`, `org-selector.component.ts`
- `org-onboarding.page.ts`, `org-create.page.ts` (aligned with business/org hub)
- `engineer.guard.ts`
- `personal-account-api.service.ts` (**required**: `getProfiles` / profile-switch APIs absent on prior HEAD)
- `shared/models/api.models.ts` (HistoryEntry / profile-adjacent fields used by activity + APIs)

**Explicitly excluded (Decision C):** CRM pages, billing page bodies, streaming search/liked/home churn, settings UI, music-player/history service rewrites, status-labels-only maps, spaces/product-surface files with **no content diff vs HEAD**, `.tmp*`, validation JSON dumps, discovery scripts (`_discover_045_closure.js`, `_closure-discovery.json`).

## Decision C — Out of scope for this commit

Unrelated package dirtiness that is not needed to satisfy Spec 045 entrypoint closure or org `organizationRequiredGuard` / `organizationModuleGuard` wiring. Those remain local WT changes.

## Validation plan

Clean `git worktree` at commit SHA → `npm ci`/`npm install` → vitest (spaces, product-surface, nav-access, organization-access) → `ng build --configuration=development`.
