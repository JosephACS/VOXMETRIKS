# Evidence — Spec 029 + integrated closure

## Code

- Package: `apps/backend/app/packages/personal_subscriptions/`
- Tests: `apps/backend/tests/test_personal_subscriptions_s029.py`
- FE: `apps/frontend/src/app/packages/personal-account/`
- Integrated seed: `apps/backend/scripts/seed_integrated_demo.py`
- Cleanup: `apps/backend/scripts/cleanup_test_organizations.py`
- Demo guide: `docs/DEMO-ACCOUNTS.md`

## Gate runs (2026-07-14)

```
apps/backend> python -m pytest tests/test_personal_subscriptions_s029.py tests/test_enterprise_golden_path_s028.py -q
19 passed

apps/backend> python -m pytest -q
799 passed

apps/frontend> npm run lint   # exit 0
apps/frontend> npm test       # 24 files / 192 tests
apps/frontend> npm run build  # exit 0

python scripts/cleanup_test_organizations.py --apply --retire-test-plans
  → archived GP Plan* test plans; warehouse music untouched

VOXMETRIKS_SEED_DEMO_ACCOUNTS=1 python scripts/seed_integrated_demo.py  # ×2 OK
python scripts/verify_demo_seed.py
  pollution_orgs []
  active_test_plans []
  household_owner_plan [('premium_family', 'active')]
```

## Pytest isolation

Session Settings override (`tests/db_isolation.py`) + closing shared DuckDB handles on bind/restore keeps pytest off the development warehouse.
