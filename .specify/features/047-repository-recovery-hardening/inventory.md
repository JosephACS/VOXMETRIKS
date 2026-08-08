# 047 — Inventario del worktree de recovery

**Worktree:** `voxmetriks-wt-047-recovery`
**Rama:** `feature/047-repository-recovery-hardening`
**Base / HEAD tip (sin commits de recovery):** `7cba24d03cd83836a0ac0a88179735df7859102b`
**Fuente dirty (solo lectura):** checkout principal `voxmetriks`
**Regla:** inventario = archivos reales presentes en este worktree (tracked modificados + untracked), no solo el último bloque de edición.

## Spec / feature pointer (tracked modified)

| Archivo | Rol |
|---------|-----|
| `.specify/feature.json` | Apunta a 047; `previous_feature_directory` = 046 |
| `.gitignore` | Conserva `data/media/`; añade `apps/backend/data/media/` y `apps/backend/data/smoke-*` (no ignora todo `apps/backend/data/`) |

## Spec / trazabilidad (untracked)

| Archivo |
|---------|
| `.specify/features/047-repository-recovery-hardening/spec.md` |
| `.specify/features/047-repository-recovery-hardening/inventory.md` |
| `.specify/features/047-repository-recovery-hardening/recovery-matrix.md` |
| `.specify/features/047-repository-recovery-hardening/runtime-baseline.md` |
| `.specify/features/047-repository-recovery-hardening/validation.md` |
| `.specify/features/047-repository-recovery-hardening/decisions.md` |

## Backend — wiring / auth (modified tracked)

| Archivo | Rol |
|---------|-----|
| `apps/backend/app/main.py` | Mounts listening/security/workpanel/reports + sync catalog; routers 046 intactos |
| `apps/backend/scripts/seed_integrated_demo.py` | Seed crea DB faltante; identity antes de RBAC |
| `apps/backend/app/packages/engagement/routes/__init__.py` | Export listening routers |
| `apps/backend/app/packages/engagement/services/app_storage.py` | Skip demo library seed si falta `dim_track` |
| `apps/backend/app/packages/engagement/services/favorite_service.py` | `/favorites` → `[]` si falta `dim_track` (sin CatalogException) |
| `apps/backend/app/packages/catalog_publishing/application/use_cases.py` | `_upsert_public_dim_track` (+ helpers) para sync |
| `apps/backend/app/packages/identity/routes/__init__.py` | Export `security_router` |
| `apps/backend/app/packages/identity/services/auth_deps.py` | Spec 037 staff gates (`require_staff_identity`, etc.) |
| `apps/backend/app/packages/personal_subscriptions/application/use_cases.py` | Household profiles + prepare-switch |
| `apps/backend/app/packages/personal_subscriptions/presentation/router.py` | Endpoints `/household/profiles*` |
| `apps/backend/app/packages/platform_ops/presentation/dependencies.py` | Bypass Spec 046 admin para `ops.view`/`ops.manage` |

## Backend — paquetes recuperados (untracked)

### Listening / engagement
| Archivo |
|---------|
| `apps/backend/app/packages/engagement/routes/listening_activity.py` |
| `apps/backend/app/packages/engagement/routes/listening_history.py` |
| `apps/backend/app/packages/engagement/services/listening_activity_service.py` |
| `apps/backend/app/packages/engagement/services/listening_history_service.py` |

### Identity / security
| Archivo |
|---------|
| `apps/backend/app/packages/identity/routes/security.py` |
| `apps/backend/app/packages/identity/services/data_classification.py` |
| `apps/backend/app/packages/identity/services/profile_security.py` |

### Catalog / publishing helpers
| Archivo | Notas |
|---------|-------|
| `apps/backend/app/packages/catalog/services/tracks/playback_availability.py` | Dependencia real de listening activity |
| `apps/backend/app/packages/catalog_publishing/application/sync_catalog.py` | Sync lifespan post-bootstrap |

### Reports / workpanel / org module access
| Archivo |
|---------|
| `apps/backend/app/packages/simple_reports/__init__.py` |
| `apps/backend/app/packages/simple_reports/ownership.py` |
| `apps/backend/app/packages/simple_reports/queries.py` |
| `apps/backend/app/packages/simple_reports/registry.py` |
| `apps/backend/app/packages/simple_reports/presentation/__init__.py` |
| `apps/backend/app/packages/simple_reports/presentation/dependencies.py` |
| `apps/backend/app/packages/simple_reports/presentation/router.py` |
| `apps/backend/app/packages/simple_reports/presentation/schemas.py` |
| `apps/backend/app/packages/complex_reports/__init__.py` |
| `apps/backend/app/packages/complex_reports/ownership.py` |
| `apps/backend/app/packages/complex_reports/queries.py` |
| `apps/backend/app/packages/complex_reports/registry.py` |
| `apps/backend/app/packages/complex_reports/router.py` |
| `apps/backend/app/packages/workpanel/__init__.py` |
| `apps/backend/app/packages/workpanel/router.py` |
| `apps/backend/app/packages/workpanel/service.py` |
| `apps/backend/app/packages/organizations/application/module_access.py` |

### Seeds / runtime / compose
| Archivo |
|---------|
| `apps/backend/requirements.runtime.txt` |
| `apps/backend/scripts/seed_044_consolidation_fixture.py` |
| `apps/backend/scripts/seed_recording_demo_fixtures.py` |
| `compose.yml` |

### Tests recuperados / añadidos
| Archivo | Estado |
|---------|--------|
| `apps/backend/tests/test_040_report_ownership.py` | Recuperado |
| `apps/backend/tests/test_044_org_isolation_reports.py` | Recuperado |
| `apps/backend/tests/test_047_artist_routers_preserved.py` | Nuevo 047 |
| `apps/backend/tests/test_047_seed_from_missing_db.py` | Nuevo 047 |
| `apps/backend/tests/test_047_lifespan_empty_warehouse.py` | Nuevo 047 |
| `apps/backend/tests/test_047_catalog_sync.py` | Nuevo 047 |
| `apps/backend/tests/test_listening_activity.py` | Recuperado |
| `apps/backend/tests/test_listening_history.py` | Recuperado |
| `apps/backend/tests/test_org_module_access.py` | Recuperado |
| `apps/backend/tests/test_profile_security.py` | Recuperado |
| `apps/backend/tests/test_simple_reports.py` | Recuperado (+ hardening org header) |
| `apps/backend/tests/test_simple_reports_all_validate.py` | Recuperado (+ org header) |
| `apps/backend/tests/test_workpanel_complex_reports.py` | Recuperado (+ periodo dinámico) |
| `apps/backend/tests/test_workpanel_semantic_metrics.py` | Recuperado |
| `apps/backend/tests/test_household_profiles_047.py` | Nuevo 047 |
| `apps/backend/tests/test_047_platform_ops_admin_access.py` | Nuevo 047 |
| `apps/backend/tests/test_roles_permissions_report.py` | Nuevo 047 |
| ~~`apps/backend/tests/test_music_search_playable.py`~~ | **Retirado** — huérfano (Unified Music Search deferred) |

## Frontend (modified tracked)

| Archivo | Rol |
|---------|-----|
| `apps/frontend/src/app/packages/artist-space/pages/artist-claim-wizard.page.ts` | Empty-state / claim UX recovery |
| `apps/frontend/src/app/packages/artist-space/pages/artist-claim-wizard.empty.spec.ts` | Empty search i18n + CTA prefill |
| `apps/frontend/src/app/core/i18n/locales/es.ts` / `en.ts` | `artistSpace.claim.noResultsTitle/Body` |
| `apps/frontend/src/app/shared/navigation/module-context.ts` | Chrome `/platform-ops` |
| `apps/frontend/src/app/shared/navigation/module-context.spec.ts` | Cobertura platform-ops |
| `apps/frontend/src/app/packages/artist-space/artist-invitation-046.spec.ts` | ESM-safe Node imports |
| `apps/frontend/src/app/core/guards/product-surface.guard.spec.ts` | ESM-safe Node imports |
| `apps/frontend/src/app/packages/analytics/phase-c-routes.spec.ts` | Alineado a redirects Workpanel/reports |
| `apps/frontend/src/app/packages/organizations/services/organizations-ui-i4.spec.ts` | Empty selector → enterprise entry |
| `apps/frontend/tsconfig.spec.json` | types Node para gate `npm test` |
| `apps/frontend/package.json` / `package-lock.json` | `@types/node` devDependency |

## Explicitamente NO en este paquete

| Capacidad | Motivo |
|-----------|--------|
| Unified Music Search (`music_search_service`, routes tracks listener writes) | `DEFERRED / REQUIRES PRODUCT DECISION` — ver `recovery-matrix.md` / `decisions.md` |
| Monetización artista / Spec 048 | Fuera de alcance |
| Merge / FF a `main` | Requiere revisión externa |
| Artefactos runtime / smoke bajo `apps/backend/data/media/` o `apps/backend/data/smoke-*` | Residuos locales; **no** forman parte del inventario 047. Gitignore explícito; smokes futuros usan dirs temporales fuera del repo |
