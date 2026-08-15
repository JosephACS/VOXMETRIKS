# Quickstart — 053 Professional Organization Journey

## Implementation order

1. Fingerprint the canonical DuckDB and use temporary copies for tests.
2. Implement schemas/catalogs and the server journey contract.
3. Harden creation, roles, member presentation and completion transactions.
4. Replace the local onboarding UI with server-driven routing.
5. Connect existing trial and 052 checkout without copying their state machines.
6. Add isolated backend/frontend/E2E acceptance.

## Required gates

```powershell
python -m pytest -q apps/backend/tests/test_spec053_organization_journey.py
python -c "from app.main import create_app; print(len(create_app().routes))"
npm --prefix apps/frontend run lint
npm --prefix apps/frontend test
npm --prefix apps/frontend run build
npm --prefix automation/playwright run e2e:053
git diff --check
```

The Playwright command must own a dedicated frontend/API and a temporary DuckDB copy. It must never reuse or mutate the canonical runtime.
