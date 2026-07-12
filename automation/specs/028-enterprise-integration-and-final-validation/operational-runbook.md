# Operational Runbook — Spec 028

Academic/demo operations for Voxmetriks enterprise closure.

## Startup sequence

```bash
# 1. ELT (if warehouse missing or stale)
make pipeline

# 2. API
cd apps/backend
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd apps/frontend && npm start
```

Env recommendations:

| Variable | Dev value |
|----------|-----------|
| `RUN_ETL_ON_BOOT` | `never` |
| `SKIP_SYSTEM_BOOT` | `0` (or `1` if warehouse pre-built) |
| `JOBS_ENABLED` | `true` locally, `false` in CI |

## Health checks

```bash
curl http://localhost:8000/health
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/platform-ops/health
```

## Optional enterprise demo seed

```bash
cd apps/backend
VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python scripts/seed_enterprise_demo.py
```

Creates synthetic org `enterprise-demo-s028` plus demo plan/subscription, CRM stubs, billing invoice/payment mock, artist/rights, campaign, report/decision, CS health, and support case — all tagged synthetic. **Never runs automatically.** See `demo-data-guide.md`.

## Test gates

```bash
# Golden path (028)
python -m pytest tests/test_enterprise_golden_path_s028.py -q

# Full backend
python -m pytest -q

# Frontend
cd apps/frontend && npm test && npm run lint && npm run build
```

## CI (`.github/workflows/ci.yml`)

- Backend pytest on push/PR
- FE lint + unit + build
- Docker compose: **not in CI** (NOT_VERIFIED)

## Incident response (academic)

1. Check `/health` and platform-ops health endpoint
2. Review `app_operational_incident` via compliance/platform_ops UI
3. Webhook dead-letter: `app_webhook_delivery` status `failed`
4. Job failures: `app_job_execution` with retry count

## Backup (conceptual)

Platform ops records backup metadata locally — **not production DR**. See 027 accepted debt.

## Credentials

| User | Password | Role |
|------|----------|------|
| demo | demo123 | user |
| admin | admin123 | admin/engineer |

## Logs

Structured logging via `app.core.logging`. Set `LOG_TO_FILES=false` in tests.
