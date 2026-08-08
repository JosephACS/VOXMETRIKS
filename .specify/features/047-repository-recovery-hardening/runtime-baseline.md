# 047 — Runtime baseline (demo local)

## Principios

1. Demo local **sin** dependencia obligatoria de PocketBase.
2. Warehouse / DuckDB de desarrollo **nunca** usado por pytest (`conftest` fuerza DB temporal).
3. Seeds idempotentes; re-ejecutar no debe romper esquemas 046.
4. `SKIP_SYSTEM_BOOT=1` / `RUN_ETL_ON_BOOT=never` en tests.
5. **Arranque con DB nueva**: `seed_integrated_demo.py` crea el archivo DuckDB si `DB_PATH` no existe; identity → RBAC → cuentas. No requiere ELT previo ni `SEED_DEMO_CRM_USERS=false`.
6. **Backend sin gold**: si falta `dim_track`, lifespan omite solo el seed de favoritos/playlists; métricas/biblioteca pueden quedar vacías.

## Compose / servicios

- `compose.yml` en la raíz del worktree (recuperado) — stack local canónico cuando se use Docker.
- Backend: `apps/backend` + `requirements.runtime.txt` (pin runtime).
- Frontend: `apps/frontend` (`npm start` / `npm run build`).

## Seeds

| Script | Uso |
|--------|-----|
| `apps/backend/scripts/seed_integrated_demo.py` | Demo B2C/B2B integrado (canónico 047) |
| `apps/backend/scripts/seed_044_consolidation_fixture.py` | Fixture consolidación 044 (orgs/reportes) |
| `apps/backend/scripts/seed_recording_demo_fixtures.py` | Fixtures de grabación / demo musical |

### Seed desde cero (documentado)

```text
cd apps/backend
set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1
set DEMO_ACCOUNT_PASSWORD=your-local-secret
set DB_PATH=..\..\data\warehouse\voxmetrik-demo.duckdb
python scripts/seed_integrated_demo.py
```

Orden interno: crear archivo/dir DuckDB → `ensure_user_tables` → `ensure_platform_rbac_tables` → cuentas/roles → org/household/fixtures.

Usuarios identity seed (app bootstrap): `demo`/`demo123`, `admin`/`admin123`, `engineer`/`engineer123` (además de las cuentas del seed integrado).

## Arranque mínimo (sin Docker)

```text
# Tras seed (DB_PATH apunta al archivo creado)
cd apps/backend
uvicorn app.main:app --reload --port 8000

cd apps/frontend
npm start
```

## Gate de arranque vacío (sin `dim_track`)

| Condición | Expectativa |
|-----------|-------------|
| DuckDB existe, sin tablas gold | Lifespan OK; sin `CatalogException` |
| Seed favoritos/playlists | Omitido si no hay `dim_track` |
| Sync catalog | Skip honesto si no hay `dim_track`; con tablas, `_upsert_public_dim_track` idempotente |

## Superficies runtime a verificar (manual / smoke)

| Ruta / API | Expectativa |
|------------|-------------|
| `create_app()` | Carga sin ImportError / AttributeError en sync |
| `/api/v1/artist-space/*`, `/artist-access/*`, `/artist-invitations/accept`, `/platform/artist-requests/*` | Presentes (046) |
| `/api/v1/workpanel` | 401 sin auth; 200 staff |
| `/api/v1/reports/simple/catalog`, `/reports/complex/catalog` | 200 staff |
| `/account/profiles` (FE) | Carga perfiles household |
| Platform Admin chrome `/platform-ops` | Tabs Ops / Audio / Artist requests |
| Artist Search (claim wizard) | `artistSpace.claim.noResultsTitle/Body` reales (nunca “Texto no disponible”) |

### Política de artefactos smoke

- **No** depositar media, logs, tokens, login JSON ni listados auxiliares bajo el worktree (`apps/backend/data/media/`, `apps/backend/data/smoke-*`).
- Usar un directorio temporal del SO (`%TEMP%` / `mktemp`) para `MEDIA_STORAGE_ROOT`, `DB_PATH` de smoke, logs, pytest tmp y secretos de sesión.
- Borrar ese árbol al terminar **aunque el smoke falle**.
- `.gitignore` cubre `data/media/`, `apps/backend/data/media/` y `apps/backend/data/smoke-*` como red de seguridad; no sustituye la política de temp fuera del repo.

## Dependencias / datos que pueden faltar

- Warehouse gold / audio sources: métricas Workpanel o listening pueden quedar en cero sin ELT/demo musical.
- ETL real: no requerido para gates 047.
- PocketBase: opcional; no bloquear demo.
