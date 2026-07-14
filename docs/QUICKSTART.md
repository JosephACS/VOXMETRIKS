# Voxmetriks — Quickstart (guía única)

Arranque local oficial. Sustituye cualquier `quickstart.md` o README legacy en subcarpetas.

**Requisitos:** Python **3.12**, Node.js **20+**, npm **10+**. Docker opcional (final de esta guía).

---

## 1. Clonar y entrar al proyecto

```bash
cd voxmetriks
```

---

## 2. Entorno Python

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

Instalar dependencias ELT + API:

```bash
pip install -r apps/backend/requirements.txt
# o: make install
```

---

## 3. Configuración

```bash
# Opción A — entorno compartido (Docker / monorepo)
cp infrastructure/environments/.env.example .env

# Opción B — solo backend local
cp apps/backend/.env.example apps/backend/.env
```

Variables relevantes (`.env`):

| Variable | Descripción |
|----------|-------------|
| `DB_PATH` | Vacío = `data/warehouse/voxmetrik.duckdb` (auto-resuelto) |
| `POCKETBASE_URL` | Fuente opcional de ingest |
| `POCKETBASE_EMAIL` / `PASSWORD` | Credenciales PocketBase |
| `CORS_ORIGINS` | Orígenes permitidos para el frontend, separados por coma |
| `HEALTH_VERBOSE` | `true` solo en dev/ops si necesitas ver ruta DB y tablas en `/health` |
| `EMAIL_PROVIDER` | `console` (default, tests) · `smtp` · `resend` |
| `SMTP_*` / `EMAIL_FROM_*` | SMTP real (Gmail: **app password**, nunca la contraseña de cuenta) |
| `RESEND_API_KEY` | Opcional si usas Resend |
| `EMAIL_SMOKE_TEST_TO` | Destinatario del smoke real (`python apps/backend/scripts/email_smtp_smoke.py --send`) |
| `FRONTEND_BASE_URL` | Base URL del frontend para enlaces en correos (p. ej. `http://127.0.0.1:4200`) |
| `APP_PUBLIC_BASE_URL` | Alias legado de `FRONTEND_BASE_URL` |

Sin PocketBase, coloca Parquet en:

```
data/bronze/raw_spotify.parquet
```

(o deja que el bootstrap del pipeline lo genere desde PocketBase).

---

## 4. Ejecutar ELT (obligatorio antes de la API)

**Pipeline canónico** (Spec 014):

```bash
make pipeline
# equivalente:
python analytics/elt/pipelines/elt_pipeline.py
```

Crea o actualiza `data/warehouse/voxmetrik.duckdb` con capas Medallion (`dim_*`, `fact_*`, `agg_*`, `ctl_*`).

`make etl` / `apps/backend/app/etl` es un **refresh runtime** (requiere warehouse + `raw_spotify`); no sustituye el pipeline canónico.

Validación opcional post-ELT:

```bash
python automation/scripts/validate_warehouse.py
```

Arranque API: `RUN_ETL_ON_BOOT=never` (recomendado en dev si el warehouse ya existe) | `auto` | `validate` | `full` (rebuild largo; preferir `make pipeline` fuera del boot). Ver [architecture/elt.md](architecture/elt.md).

---

## 5. Levantar API

Desde `apps/backend/`:

```bash
cd apps/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verificar:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

- Documentación interactiva: http://localhost:8000/docs  
- OpenAPI: prefijo `/api/v1`
- `/health` público no expone ruta de DB ni nombres de tablas por defecto.

---

## 6. Levantar frontend

En otra terminal:

```bash
cd apps/frontend
npm install
npm start
```

Abrir http://localhost:4200

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `demo` o `demo@voxmetrik.io` | `demo123` | Usuario estándar |
| `admin` o `admin@voxmetrik.io` | `admin123` | Engineer (+ `/elt-pipeline`, `/explorer`) |

### Cuentas demo (B2C + B2B) — cierre integrado

Guía completa (sin contraseñas): [`docs/DEMO-ACCOUNTS.md`](../docs/DEMO-ACCOUNTS.md)

```bash
cd apps/backend
# limpia orgs/planes de pytest (no toca dim_track / catálogo musical)
python scripts/cleanup_test_organizations.py --apply --retire-test-plans

set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1
set DEMO_ACCOUNT_PASSWORD=TU_SECRETO_LOCAL
python scripts/seed_integrated_demo.py
# re-ejecutar = idempotente
```

Contraseña: variable **`DEMO_ACCOUNT_PASSWORD`** (solo hash en DB; placeholder en `.env.example`).

| Username | Demostración | Rutas |
|----------|--------------|-------|
| `listener.free` | Free personal | `/home`, `/account/plans` |
| `listener.premium` | Premium Individual | `/account/subscription`, `/account/billing` |
| `household.owner` | Familiar + miembros | `/account/household` |
| `platform.admin` | Catálogos / ops | `/platform-ops` |
| `sales.manager` | CRM comercial | `/crm/*` |
| `organization.owner` | Org Professional | `/organizations/*`, `/subscriptions/*` |
| `finance.manager` | Billing org | `/billing/*` |

Planes **personales** (`/account/*`) ≠ planes **empresariales** (`/subscriptions/*`).

---

## 7. Tests y smoke (opcional)

```bash
# Backend (suite completa)
cd apps/backend
python -m pytest -q

# Frontend
cd apps/frontend
npm test
npm run lint
npm run build
```

Smoke contra la API real (requiere backend levantado):

```bash
python ../automation/scripts/smoke_api.py --base-url http://localhost:8000
python ../automation/scripts/smoke_user_journey.py --base-url http://localhost:8000
```

Playwright (`automation/playwright`) requiere `npm install` en esa carpeta; **no está instalado por defecto** en todos los entornos.

La regresión cubre health, login, logout server-side, RBAC engineer, explorer, protección de datos sensibles, búsqueda y limpieza de textos. El journey agrega favoritos, playlists, recomendaciones e historial.

---

## 8. Docker (alternativa)

```bash
docker compose -f infrastructure/docker/docker-compose.yml up --build
```

- `pipeline` — job one-shot ELT  
- `api` — http://localhost:8000 (tras pipeline OK)  
- `pocketbase` — http://localhost:8090 (opcional)

Re-ejecutar solo ELT:

```bash
docker compose run --rm pipeline
```

### Otra laptop/PC desde cero (cero configuración manual de datos)

El dataset fuente (`infrastructure/pocketbase/pb_data`) viaja en git, así que el pipeline reconstruye el DuckDB solo. Tres pasos:

```bash
git clone <repo>
cd voxmetriks
cp .env.example .env          # Windows: copy .env.example .env
docker compose -f infrastructure/docker/docker-compose.yml up --build
```

- **`.env` no está en git:** créalo desde `.env.example` y completa `POCKETBASE_EMAIL` / `POCKETBASE_PASSWORD`.
- **`YOUTUBE_API_KEY` opcional:** `yt-dlp` resuelve el audio sin cuota; la API de YouTube es solo respaldo.
- El **warehouse DuckDB no se versiona** (está en `.gitignore`); se genera en el primer arranque. La caché de audio (`app_track_audio_source`) se llena al reproducir y no viaja entre máquinas; precalentarla es opcional con `python automation/scripts/resolve_audio_youtube.py --limit 2000`.

---

## Endpoints de referencia (API v1)

| Área | Ejemplos |
|------|----------|
| Identidad | `POST /api/v1/users/login`, `POST /api/v1/users/register`, `GET /api/v1/users/me` |
| Catálogo (streaming) | `GET /api/v1/catalog/artists`, `/genres`, `/tracks` |
| Artistas (negocio) | `GET/POST /api/v1/artists` (perfiles B2B; UI `/artist-profiles`) |
| Empresa (ejemplos) | `/organizations`, `/crm`, `/plans`, `/billing`, `/campaigns`, `/compliance`, `/platform-ops` |
| Biblioteca | `GET/POST /api/v1/playlists`, `GET/POST /api/v1/favorites/{id}` |
| Analítica | `GET /api/v1/stats/summary`, `/api/v1/analytics/trending` |
| Ingeniería | `GET /api/v1/analytics/warehouse`, `POST /api/v1/stats/synthetic` |
| Explorer | `GET /api/v1/analytics/explorer/tables`, `.../preview/{table}` |

Listado completo en Swagger: `/docs`.

---

## Solución de problemas

### `Database not found` / health `degraded`

Ejecuta el ELT (paso 4). Verifica que exista `data/warehouse/voxmetrik.duckdb`.

### `SerializationError` (DuckDB)

Versión incompatible del archivo. Borra el `.duckdb` y vuelve a correr el pipeline.

### Puerto 8000 ocupado

```bash
uvicorn app.main:app --reload --port 8001
```

Actualiza `apps/frontend/src/environments/environment.ts` → `apiUrl`.

### Frontend no conecta a API

Confirma `CORS_ORIGINS` e incluye `http://localhost:4200`. Verifica también que `apiUrl` apunte a `http://localhost:8000/api/v1`.

---

## 9. Capa empresarial (opcional)

Estado de cierre: **ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT** (Spec 028, con 024 reporting + 025 CS/support).

Documentación: [automation/specs/028-enterprise-integration-and-final-validation/](../automation/specs/028-enterprise-integration-and-final-validation/). Guion demo: [`demo-script.md`](../automation/specs/028-enterprise-integration-and-final-validation/demo-script.md).

Seed demo **explícito y opt-in** (marcado synthetic; no usar en producción):

```bash
cd apps/backend
# Windows PowerShell
$env:VOXMETRIKS_SEED_ENTERPRISE_DEMO="1"; python scripts/seed_enterprise_demo.py
# Linux / macOS
VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python scripts/seed_enterprise_demo.py
```

Detalle: [`demo-data-guide.md`](../automation/specs/028-enterprise-integration-and-final-validation/demo-data-guide.md).

Nota: rutas `/api/v1/artists` de negocio ≠ catálogo streaming (`/api/v1/catalog/artists`). UI empresarial de artistas: `/artist-profiles`.

---

## Documentación relacionada

- [README.md](../README.md) — visión y estructura del repo  
- [automation/specs/028-enterprise-integration-and-final-validation/](../automation/specs/028-enterprise-integration-and-final-validation/) — cierre empresarial  
- [docs/uml/README.md](uml/README.md) — diagramas PlantUML  
- [../voxmetriks-entregas](../voxmetriks-entregas) — entrega académica TGA07 (docx)
