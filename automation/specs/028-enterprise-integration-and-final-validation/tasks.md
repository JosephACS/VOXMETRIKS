# Tasks — Spec 028

## T1 — Scaffold spec directory

- [x] Create `automation/specs/028-enterprise-integration-and-final-validation/`
- [x] Create `evidence/` subdirectory
- [x] Point `.specify/feature.json` (pre-existing)

## T2 — Core spec documents

- [x] `spec.md`
- [x] `plan.md`
- [x] `architecture-as-implemented.md`
- [x] `enterprise-capability-status.md`

## T3 — Validation documents

- [x] `golden-path-validation.md`
- [x] `security-validation.md`
- [x] `data-validation.md`
- [x] `performance-validation.md`
- [x] `final-validation.md`
- [x] `final-traceability.md`

## T4 — Operations & closure

- [x] `operational-runbook.md`
- [x] `demo-data-guide.md`
- [x] `demo-script.md`
- [x] `deployment-limitations.md`
- [x] `accepted-debt.md`
- [x] `deferred-items.md`
- [x] `project-closure.md`
- [x] `evidence/spec-closure.md`
- [x] `checklist.md`

## T5 — Code: demo seed

- [x] `apps/backend/scripts/seed_enterprise_demo.py`
- [x] Env gate `VOXMETRIKS_SEED_ENTERPRISE_DEMO=1`
- [x] DEMO banner; `is_demo` flags; safe if tables missing

## T6 — Code: golden path test

- [x] `apps/backend/tests/test_enterprise_golden_path_s028.py`
- [x] Chain: login → org → plans → campaigns → biz-analytics → compliance → platform-ops
- [x] Assert 404 for support, customer-success, reporting/reports

## T7 — Repo documentation updates

- [x] `README.md` enterprise status
- [x] `TRACEABILITY-MASTER.md` 028 closure section

## T8 — FE nav check

- [x] Billing reconciliation link in dashboard-layout (already present)

## T9 — Execute gates

- [x] `pytest tests/test_enterprise_golden_path_s028.py -q`
- [ ] Full backend pytest ~737 (revalidating — not 028 blocker)

## Dependencies

```text
T1 → T2–T4 (parallel docs)
T5, T6 → T9
T7 after T2 (status text)
T4 closure after T9 golden path PASS
```
