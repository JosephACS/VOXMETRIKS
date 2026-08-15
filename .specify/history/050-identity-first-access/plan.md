# Implementation Plan: Identity and First Access Orchestration

**Branch**: `050-identity-first-access` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

## Summary

Integrate existing identity and space capabilities behind a single backend-authoritative session bootstrap and one frontend post-auth orchestrator. Preserve legacy endpoints as adapters while removing their authority over navigation.

## Technical Context

**Language/Version**: Python 3.12; TypeScript/Angular 21

**Primary Dependencies**: FastAPI, Pydantic, DuckDB, Angular standalone components/RxJS

**Storage**: Existing DuckDB `app_*` tables; avoid new persistence unless research proves it necessary

**Testing**: pytest, Angular/Vitest suite, Playwright

**Target Platform**: Local/demo web application, desktop and mobile-responsive browser

**Constraints**: No rewrite; no raw PAN/CVV; no real MFA; no module deletion; backend remains authorization authority

## Constitution Check

- Business journey and actors precede UI changes.
- Security/RBAC and organization isolation are P0.
- Unknown, unavailable and denied remain distinct states.
- Demo/development information is never presented as production truth.
- Tests must run against isolated temporary databases without relying on order.
- No canonical dataset mutation during automated tests.

## Technical design

1. Fix per-connection schema readiness so identity tests are isolated.
2. Introduce `GET /api/v1/session/bootstrap` as an application composition endpoint; reuse domain services rather than duplicating SQL.
3. Introduce explicit context activation returning the same manifest shape.
4. Implement a frontend post-auth orchestrator used by login, verify, Google, restored session and invitation return.
5. Make navigation and guards consume the manifest; retain old route helpers only as transition adapters.
6. Add minimal first-run intent UI and connect Personal/Artist/Organization entry actions.
7. Apply the shared form contract to auth and organization creation/onboarding touched by this feature.

## Source scope

```text
apps/backend/app/packages/identity/
apps/backend/app/packages/organizations/
apps/backend/app/packages/artists/identity_access/
apps/backend/app/packages/personal_subscriptions/
apps/backend/app/packages/platform_rbac/
apps/backend/tests/

apps/frontend/src/app/pages/login/
apps/frontend/src/app/core/guards/
apps/frontend/src/app/core/services/auth.service.ts
apps/frontend/src/app/core/spaces/
apps/frontend/src/app/packages/personal-account/
apps/frontend/src/app/packages/organizations/
apps/frontend/src/app/packages/artist-space/
automation/playwright/e2e/
```

## Existing baseline defects included

- `ensure_user_tables()` can skip `app_user` in a fresh database when global schema readiness is true; 13 directed security tests currently fail from this order dependency.
- Frontend lint currently has two literal-property errors outside auth (`complex-reports.page.ts`, `workpanel.page.ts`); fix mechanically as release gates, without expanding product scope.
- `npm run lint` scans a blocked frontend `.pytest_cache` on this host; validation may target `src` or remove only the verified temporary artifact.

## Package boundary for Cursor

One implementation package. Cursor may edit only the source scope above plus targeted shared schemas/i18n and the two mechanical lint files. No dashboard, checkout, publishing, CRM, royalties, ELT or dataset work.
