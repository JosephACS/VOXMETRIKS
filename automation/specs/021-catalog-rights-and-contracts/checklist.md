# Checklist — Spec 021

## Schema
- [X] 11 tables created idempotently
- [X] CHECK constraints on status, rights_type, ownership_percentage
- [X] Wired in main.py + conftest.py

## Backend
- [X] 16 use case groups implemented
- [X] Sweep-line overlap detection
- [X] Approval workflow
- [X] Coverage query
- [X] Router at `/api/v1/catalog-rights`
- [X] 98 pytest tests PASS

## Permissions
- [X] 6 `rights.*` permissions seeded
- [X] Role matrix per spec

## Frontend
- [X] API service + models
- [X] Pages: assets, releases, contracts, conflicts (+ coverage/approvals on detail pages)
- [X] Routes + nav + i18n
- [X] L4 unit smoke tests

## Docs & closure
- [X] Full spec folder
- [X] evidence/spec-closure.md CLOSED_WITH_ACCEPTED_DEBT
- [X] TRACEABILITY-MASTER updated

## Accepted debt (explicit)
- [ ] Playwright E2E NOT_VERIFIED
- [ ] No auto-expiry on valid_to
- [ ] warehouse_album_id unvalidated
