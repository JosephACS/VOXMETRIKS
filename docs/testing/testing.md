# Testing — Pruebas

## Stack

| Herramienta | Uso |
|-------------|-----|
| pytest 8.2 | Framework test |
| pytest-cov | Cobertura |
| FastAPI TestClient | Tests API integration |
| DuckDB test DB | Warehouse aislado |

## Estructura

```
apps/backend/tests/
├── conftest.py              # Fixtures: client, auth headers, test DB
├── test_api.py              # Login, playlists, favorites
├── test_enterprise_api.py   # Enterprise /api/v1 envelope
├── test_production_infra.py # Errors, headers, cache, pagination
├── test_recommendation_engine.py
├── test_recommendation_service.py
├── test_orchestrator.py
├── test_etl_pipeline.py
├── test_gold_pipeline.py
├── test_data_validation.py
├── test_auth_security.py
├── test_smoke_regression.py
└── ...
```

**Total archivos test:** 21  
**Tests passing:** ~110 (1 skipped)

## Ejecución

```bash
cd apps/backend
pip install -r requirements.txt
pytest tests/ -v
pytest tests/ -q --ignore=tests/test_integration.py
pytest tests/test_enterprise_api.py -v
```

## Cobertura

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

**Cobertura backend (`app/`):** ~75% (6,045 statements, 1,538 missed)

## Fixtures clave

| Fixture | Descripción |
|---------|-------------|
| `client` | TestClient con app completa |
| `auth_headers` | Token demo user |
| `admin_auth_headers` | Token engineer admin |

Variables en conftest:
- `SKIP_SYSTEM_BOOT=1`
- `GLOBAL_RATE_LIMIT=0`
- `LOG_TO_FILES=false`

## Categorías de tests

| Categoría | Archivos | Qué valida |
|-----------|----------|------------|
| Unit | recommendation_engine, display_text | Lógica aislada |
| Repository | enterprise_api (indirect) | SQL + envelope |
| API | test_api, test_api_v2, test_enterprise_api | HTTP status + schema |
| Integration | test_etl_pipeline, test_orchestrator | Pipeline E2E |
| Security | test_auth_security, test_analytics_security | RBAC, datos sensibles |
| Smoke | test_smoke_regression | Regresiones críticas |
| Production | test_production_infra | Error envelope, headers |

## Smoke tests (runtime)

Con backend corriendo:

```bash
uvicorn app.main:app --reload --port 8000
python automation/scripts/smoke_api.py --base-url http://localhost:8000
python automation/scripts/smoke_user_journey.py --base-url http://localhost:8000
```

Validan: health, login, favoritos, playlists, recomendaciones, historial.

## Frontend tests

```bash
cd apps/frontend
npm test   # Karma/Jasmine (MusicPlayerService.spec.ts)
ng build --configuration development
```

## E2E (Playwright)

**Estado:** 45/45 passed (servidores externos, sin webServer managed).

```powershell
# Terminal 1 — backend SOLO para E2E (no usar en dev diario)
npm run e2e:backend

# Terminal 2 — frontend
npm run e2e:frontend

# Terminal 3 — tests
npm run e2e
```

Variables **solo** en entorno E2E (ver `apps/backend/.env.e2e.example`):

- `E2E=1`
- `GLOBAL_RATE_LIMIT=0`
- `AUTH_RATE_LIMIT=0`

En dev/prod los defaults son `AUTH_RATE_LIMIT=20` y `GLOBAL_RATE_LIMIT=120` (`apps/backend/.env.example`).  
Si `GLOBAL_RATE_LIMIT=0` se define fuera de pytest/E2E, el backend lo ignora y usa 120.

Detalle de cierre: [v2-delivery-closure.md](../12-audit/v2-delivery-closure.md)

## CI recomendado

```yaml
- pip install -r backend/requirements.txt
- pytest tests/ -q --cov=app --cov-fail-under=70
- cd apps/frontend && npm ci && ng build
```

## Qué falta (roadmap testing)

- [ ] Tests E2E Playwright/Cypress
- [ ] Contract tests OpenAPI
- [ ] Load tests (k6) en `/dashboard/overview`
- [ ] Mutation testing en recommendation engine
