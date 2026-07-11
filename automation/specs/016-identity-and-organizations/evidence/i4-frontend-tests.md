# I4 — Frontend tests

**Status**: COMPLETE (unit) · E2E NOT_VERIFIED

## Unit (Vitest / ng test)

Archivos:

- `services/organizations-i4.spec.ts` — API, context, routes, no-localStorage authz
- `services/organizations-ui-i4.spec.ts` — selector, none, create/slug conflict, accept, audit sanitize

Resultado: **77/77 PASS** (suite completa frontend, 2026-07-11).

## Cobertura I4 pedida

| Tema | Cubierto |
|------|----------|
| API service | sí |
| store/context + switch limpia permisos | sí |
| selector / none | sí |
| create + slug conflict | sí |
| invitation returned-once | sí (API) |
| accept error mapping | sí |
| audit sanitization | sí |
| rutas personales sin org | sí (route registry) |
| onboarding / members UI deep | parcial vía rutas + API; páginas con HTTP mocks en create/accept |

## Lint / build

- lint: 0 errors (warnings preexistentes + 1 unused fix en org-none)
- build: OK; budgets WARN preexistentes (initial 644.52 kB > 550 kB; home.css)

## Backend contract smoke

`pytest apps/backend/tests/test_organizations_api_i3.py` — PASS (sin cambios de contrato).

## E2E Playwright

**NOT_VERIFIED** — `automation/playwright` solo tiene `playwright.config.ts`; no hay specs de org flows.
