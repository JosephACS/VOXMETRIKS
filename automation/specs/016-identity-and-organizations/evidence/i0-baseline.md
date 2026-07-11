# Spec 016 — I0 Baseline (pre-implementación)

**Fecha:** 2026-07-11  
**Estado I0:** COMPLETE  
**Alcance:** registro del estado actual; **sin** tablas org, endpoints nuevos ni UI org.

## Activación tooling

| Ítem | Valor |
|------|-------|
| `.specify/feature.json` | `automation/specs/016-identity-and-organizations` |
| Constitución | **no** modificada |
| TRACEABILITY-MASTER | **no** modificado |

## Backend

| Check | Resultado | Evidencia |
|-------|-----------|-----------|
| pytest suite | **PASS** — 168 tests, EXIT=0 | `_baseline_pytest.txt` |
| FastAPI /health | **PASS** — 200, `status=healthy`, `db_connected=true` | `_baseline_auth.txt` |
| Login smoke | **PASS** — `POST /api/v1/users/login` demo/demo123 → 200 + token | `_baseline_auth.txt` |
| `/me` bearer | **PASS** — `GET /api/v1/users/me` → 200 | `_baseline_auth.txt` |
| Logout | **PASS** — `POST /api/v1/users/logout` → 200 | `_baseline_auth.txt` |
| Bearer post-logout | **PASS** — `/me` → 401 | `_baseline_auth.txt` |

Warnings/fallos no relacionados: **no corregidos** (política I0).

## Frontend

| Check | Resultado | Evidencia |
|-------|-----------|-----------|
| lint | **PASS** — 0 errors, 13 warnings preexistentes, EXIT=0 | `_baseline_lint.txt` |
| unit tests | **PASS** — 12 files / 59 tests, EXIT=0 | `_baseline_unit.txt` |
| build | **PASS** — EXIT=0; budget warnings (initial 628.79 kB; home.css) | `_baseline_build.txt` |
| rutas identity | **PASS** — `login`, `users` (perfil/`shell.myProfile`), `settings` | `_baseline_fe_routes.txt` |

Nota: no existe path `profile`; el perfil actual es `path: 'users'`.

## Datos / warehouse

| Check | Resultado | Evidencia |
|-------|-----------|-----------|
| `validate_warehouse.py` | **PASS** — 900,000 facts; DB 261.3 MB; 29 parquet | `_baseline_warehouse.txt` |
| Esquema identity | **PASS** — ver `_baseline_schema.txt` y sección abajo | `_baseline_schema.txt` |

DB: `data/warehouse/voxmetrik.duckdb`

### Row counts (I0)

| Tabla | COUNT(*) |
|-------|----------|
| `app_user` | **5** |
| `app_session` | **243** |
| `app_email_code` | **0** |

### Columnas reales

**app_user (11):** id, username, email, password_hash, plan, favorite_genre, created_at, preferences_json, role, email_verified, auth_provider  

**app_session (4):** token, user_id, created_at, expires_at  

**app_email_code (6):** email, code_hash, purpose, expires_at, attempts, created_at  

Restricciones: PK/UNIQUE en user id/username/email; PK session `token`; PK email_code `email`. Sin FK DuckDB formal `session.user_id → user.id`.

### Mecanismo actual que crea/modifica tablas APP

- `ensure_user_tables` / migraciones aditivas en `apps/backend/app/packages/identity/services/user_storage.py`
- Invocado en lifespan de `apps/backend/app/main.py` junto a `ensure_app_tables`, luego `mark_schema_ready()`
- Guard `schema_ready()` evita re-DDL repetido en el mismo proceso
- Patrón: `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE … ADD COLUMN` idempotente

## Otros

| Check | Resultado |
|-------|-----------|
| Docker | **NOT_AVAILABLE** — no en PATH (`_baseline_docker.txt`) — no se afirma PASS |
| Playwright | CLI **1.61.1** instalable vía npx; **no** en `package.json` de frontend; e2e no ejecutado en I0 |

## Código de aplicación en I0

**Ningún cambio** a backend/frontend de producto. Solo activación `feature.json` + evidencia/docs OpenSpec 016.
