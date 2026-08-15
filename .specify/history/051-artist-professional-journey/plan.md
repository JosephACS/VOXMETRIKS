# Implementation Plan: Professional Artist Journey

**Branch**: `codex/051-artist-professional-journey` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

## Summary

Connect existing artist identity/access and catalog-publishing capabilities behind one Artist Space journey, while retaining Organization Catalog for multi-artist businesses. Replace independent sentinel organization `0` with hidden real tenants, add artist-scoped publishing adapters, consolidate frontend navigation/forms and prove RBAC/isolation end to end.

## Technical Context

**Language/Version**: Python 3.12, TypeScript/Angular current workspace
**Primary Dependencies**: FastAPI, Pydantic, DuckDB, Angular, RxJS
**Storage**: Existing canonical DuckDB application tables; additive idempotent schema only
**Testing**: pytest, Angular/Vitest, Playwright
**Target Platform**: Web SPA + API; desktop and mobile responsive
**Project Type**: Monorepo web application
**Constraints**: no canonical dataset mutation in tests; no duplicated publishing engine; no raw PAN/CVV/KYC; no silent errors
**Scale/Scope**: artist identity/access, profile/team, release submission/review and related navigation

## Constitution Check

- **P1 evolution**: reuse artists, organizations and publishing; no rewrite.
- **P2/P14 ownership**: artist profile/membership remain in artists; release state remains in catalog_publishing.
- **P4/P6**: only `app_*` operational tables mutate; warehouse is read/link target.
- **P9 contract-first**: Pydantic DTOs and frontend models follow [contracts/artist-journey-api.md](contracts/artist-journey-api.md).
- **P13/P15**: hidden tenant isolation, artist membership authority, platform review and separation of duties.
- **P16**: request and publishing transitions remain explicit.
- **P20**: external distribution and production-grade storage are not claimed.

No constitutional exception is required.

## Implementation Strategy

### 1. Baseline and preservation

Record branch/status and canonical DB hash. Preserve the pre-existing unstaged Listener closure files; they are not implementation input for 051 and Cursor MUST NOT overwrite them.

### 2. Artist tenancy and identity

- Extend artist schema/profile/request DTOs idempotently.
- Implement an artist-workspace provisioner by composing Organization use cases/repositories inside one serialized transaction boundary.
- Backfill only application artist profiles still using sentinel `0`.
- Enrich artist discovery with management state and allowed action.
- Extend role permissions and audit all review/provisioning decisions.

### 3. Artist-scoped publishing adapter

- Add artist-membership dependencies for catalog view, draft mutation and submit.
- Resolve organization from the selected artist profile server-side.
- Call existing catalog-publishing use cases; do not reproduce SQL/state transitions.
- Add Platform Ops independent-submission review adapter with explicit audit and self-review prevention.

### 4. Frontend canonicalization

- Replace the claim page with a choice-driven wizard and human status cards.
- Consolidate Artist Space tracks/releases as Music with role-aware CTA.
- Add editable profile and professional team/access controls.
- Reuse/refactor the release wizard so Artist Space fixes the active artist and Organization Catalog requires an explicit artist selector.
- Remove false-success `catchError` paths.
- Keep legacy routes as redirects/compatibility; filter navigation by permissions.

### 5. Verification

Run directed tests during implementation. At closure run full backend, frontend lint/test/build and Playwright desktop/mobile. Use isolated DB copies and confirm canonical DB unchanged.

## Project Structure

```text
.specify/features/051-artist-professional-journey/
├── spec.md
├── research.md
├── data-model.md
├── plan.md
├── quickstart.md
├── tasks.md
└── contracts/artist-journey-api.md

apps/backend/app/packages/artists/
├── identity_access/
├── application/
├── infrastructure/
└── presentation/

apps/backend/app/packages/catalog_publishing/
├── application/
└── presentation/

apps/frontend/src/app/packages/artist-space/
apps/frontend/src/app/packages/artists/
apps/frontend/src/app/packages/catalog-publishing/
apps/frontend/src/app/core/spaces/

apps/backend/tests/test_spec051_*.py
automation/playwright/e2e/tests/artist-professional-journey.spec.ts
```

## Explicit non-goals

- No payment/royalty/AI/dashboard work.
- No new frontend design system.
- No external DSP publishing.
- No deletion of compatibility routes in this package.
- No full suites after every small edit; directed tests first, full gates once at closure.
