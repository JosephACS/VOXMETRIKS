# Tasks 049 — TAF14 strategic AGG closure

## Spec Kit

- [x] T001 Create Spec 049 (`spec.md`, `plan.md`, `tasks.md`) under `.specify/features/049-taf14-strategic-agg-closure/`
- [x] T002 Point `.specify/feature.json` at active Spec 049; note CAPABILITY_MAP family 10 in progress

## Backend — schema & refresh

- [x] T010 Add `agg_strategic_kpi_period` DDL + logical idempotent key to `business_analytics` schema
- [x] T011 Implement OE-01…OE-08 mapping + transactional refresh (reuse MRR/ARR/ROI/warehouse/quality/ctl/audit/health)
- [x] T012 Ensure null/unavailable never coerced to zero; propagate synthetic/proxy; no FX invention

## Backend — API / RBAC

- [x] T020 Schemas for strategic KPI row + overview (eight objectives ordered)
- [x] T021 Endpoints: `POST .../strategic/refresh`, `GET .../strategic/overview`
- [x] T022 Org isolation; platform-global only for Platform Admin; deny without data leak
- [x] T023 Embed strategic period rows into executive report snapshot payload when available

## Frontend

- [x] T030 Models + API service for strategic overview/refresh
- [x] T031 Consolidate dashboard: “Dirección estratégica”, eight cards, badges, evidence/report/decision links
- [x] T032 i18n ES/EN; responsive 1366×768 / 390×844; no business “IA” label

## Tests & gates

- [x] T040 Backend directed tests (schema, refresh, isolation, null, proxy, FX, ROI, overview, report, decision)
- [x] T041 Frontend directed tests (API + dashboard)
- [x] T042 Gates: backend pytest, create_app, npm lint/test/build, git diff --check, Spec MD links, canonical DB hash
- [x] T043 Cleanup ports 8000/4200 + `.pytest-codex-049-final`; Spec closed to history; commit/PR (no force)
