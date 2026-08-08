# 047 — Validation checklist

## Git gates (pre-commit local)

- Rama: `feature/047-repository-recovery-hardening`
- Base esperada: `7cba24d03cd83836a0ac0a88179735df7859102b`
- `git diff --cached` vacío (0 staged) hasta instrucción de commit
- `git diff --check` limpio

## Backend (pytest, cwd `apps/backend`)

| Suite | Comando |
|-------|---------|
| Preservación 046/047 | `python -m pytest tests/test_047_artist_routers_preserved.py -q` |
| Artist identity 046 | `python -m pytest tests/test_artist_identity_046.py -q` |
| Seed DB inexistente | `python -m pytest tests/test_047_seed_from_missing_db.py -q` |
| Lifespan sin gold | `python -m pytest tests/test_047_lifespan_empty_warehouse.py -q` |
| Catalog sync | `python -m pytest tests/test_047_catalog_sync.py -q` |
| Listening | `python -m pytest tests/test_listening_activity.py tests/test_listening_history.py -q` |
| Simple reports | `python -m pytest tests/test_simple_reports.py tests/test_simple_reports_all_validate.py tests/test_roles_permissions_report.py -q` |
| Workpanel / complex | `python -m pytest tests/test_workpanel_complex_reports.py tests/test_workpanel_semantic_metrics.py -q` |
| Org isolation | `python -m pytest tests/test_044_org_isolation_reports.py -q` |
| Profile security | `python -m pytest tests/test_profile_security.py -q` |
| Personal subscriptions | `python -m pytest tests/test_personal_subscriptions_s029.py -q` |
| Household profiles 047 | `python -m pytest tests/test_household_profiles_047.py -q` |
| Platform Ops | `python -m pytest tests/test_platform_ops_api_r3.py tests/test_platform_ops_security_r5.py tests/test_047_platform_ops_admin_access.py -q` |
| Module access | `python -m pytest tests/test_org_module_access.py -q` |

## Frontend (cwd `apps/frontend`)

| Gate | Comando |
|------|---------|
| Unit tests (oficial) | `npm test` |
| Build | `npm run build` |
| Artist Space / spaces (dirigido) | `npx vitest run src/app/packages/artist-space src/app/core/spaces src/app/shared/navigation/module-context.spec.ts` |

## Runtime smoke (sin workaround)

Usar **rutas temporales fuera del repositorio** para:

- `MEDIA_STORAGE_ROOT`
- logs de uvicorn/frontend
- base temporal de pytest / DuckDB de smoke
- reportes auxiliares (`smoke-routes`, inventories, etc.)
- tokens y respuestas de login

Limpiar esos directorios **siempre** (también si el smoke falla). No escribir bajo `apps/backend/data/media/` ni `apps/backend/data/smoke-*` en el worktree.

1. `DB_PATH` a ruta inexistente (temp fuera del repo) → `seed_integrated_demo.py` con flags documentados → OK.
2. Backend `uvicorn` sobre esa DB → sin `CatalogException` / `AttributeError`.
3. Frontend `npm start` → `/account/profiles`, `/platform-ops`, claim search empty con textos reales.

## Criterios de aceptación de seguridad en reportes

1. Org-scoped sin `X-Organization-Id` → **400**
2. Org ajena / membresía inactiva → **403**
3. Miembro activo + header → **200**
4. Global sin header → **200**
5. No convertir org-scoped en global para “hacer pasar” tests

## Unified Music Search

- **No** validar en este paquete (deferred). Test huérfano retirado.
