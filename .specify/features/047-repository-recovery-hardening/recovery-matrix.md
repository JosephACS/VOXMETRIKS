# 047 — Recovery matrix

Estado de cada capacidad recuperada respecto a dirty vs `origin/main@7cba24d0`.

| Capacidad | Spec origen | Estado en recovery | Evidencia | Notas |
|-----------|-------------|--------------------|-----------|-------|
| Artist Space routers (046) | 046 | **PRESERVED** | `main.py` mounts + `test_047_artist_routers_preserved.py` + `test_artist_identity_046.py` | No tocar contract invite token-in-body |
| Workpanel API | 037/044 | **RECOVERED** | `workpanel/` + mount `/api/v1/workpanel` | Periodo vía default / `available_periods` |
| Simple reports | 037/040/044 | **RECOVERED** | `simple_reports/` + catalog/data | Org-scoped exige `X-Organization-Id` |
| Complex reports | 037/044 | **RECOVERED** | `complex_reports/` | Staff gate Spec 037 |
| Listening history/activity | 035 | **RECOVERED** | routes + services + tests | Depende de `playback_availability` |
| Profile security / PIN | B2C | **RECOVERED** | `profile_security.py` + security routes | |
| Household profiles / prepare-switch | B2C | **RECOVERED** | personal_subscriptions router/use_cases + tests 047 | Sin emails en listado; prepare-switch solo hint |
| Module access | 044 | **RECOVERED** | `module_access.py` + `test_org_module_access.py` | |
| Sync published → catalog | 031/044 | **HARDENED** | `sync_catalog` + `_upsert_public_dim_track` + `test_047_catalog_sync.py` | Idempotente; fallo real no se disfraza |
| Empty warehouse lifespan | 047 | **HARDENED** | `_seed_demo_library` skip sin `dim_track` + `test_047_lifespan_empty_warehouse.py` | Sin `CatalogException` |
| Seed integrated from missing path | 047 | **HARDENED** | `seed_integrated_demo._prepare_seed_database` + identity-before-RBAC + `test_047_seed_from_missing_db.py` | Sin ELT / sin CRM flag override |
| Platform Ops admin access | 027 + 046 def | **HARDENED** | `dependencies.py` + tests 047 | Identity `admin` OR CRM `platform_admin` → `ops.view`/`ops.manage` only |
| roles-permissions report | 037 | **FIXED** | `COALESCE(r.display_name, r.code)` | Antes fallaba silencioso vía `_safe_query` |
| Demo seeds / compose | runtime | **RECOVERED** | `compose.yml`, seed scripts, `requirements.runtime.txt` | Ver `runtime-baseline.md` |
| FE module chrome `/platform-ops` | 043/047 | **RECOVERED** | `module-context.ts` | |
| Artist claim / search empty state | 046/047 | **FIXED** | i18n `noResultsTitle/Body` + claim empty spec | Unified Search sigue deferred |
| Unified Music Search | dirty | **DEFERRED / REQUIRES PRODUCT DECISION** | Test huérfano retirado; **no** se copia `music_search_service` ni writes listener en `catalog/routes/tracks.py` | Implica endpoints + mutaciones de catálogo no aprobadas en 047 |
| Monetización artista | 048 | **OUT OF SCOPE** | — | |
| PocketBase obligatorio | — | **NOT REQUIRED** | Runtime local sin PB | |

## Leyenda

- **PRESERVED** — ya en tip 046; no degradar.
- **RECOVERED** — traído del dirty e integrado.
- **HARDENED / FIXED** — recuperado + corrección de defecto de auditoría.
- **DEFERRED / REQUIRES PRODUCT DECISION** — no incluir en este paquete.
- **OUT OF SCOPE** — prohibido por Spec 047.
