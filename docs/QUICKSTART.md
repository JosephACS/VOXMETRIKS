# Voxmetriks — Quickstart (guía única)

Arranque local oficial.

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
| `POCKETBASE_URL` | Fuente opcional de ingest (fuera de Compose) |
| `POCKETBASE_EMAIL` / `PASSWORD` | Credenciales PocketBase si se usa esa fuente |
| `CORS_ORIGINS` | Orígenes permitidos para el frontend, separados por coma |
| `HEALTH_VERBOSE` | `true` solo en dev/ops si necesitas ver ruta DB y tablas en `/health` |
| `EMAIL_PROVIDER` | `console` (default, tests) · `smtp` · `resend` |
| `SMTP_*` / `EMAIL_FROM_*` | SMTP real (Gmail: **app password**, nunca la contraseña de cuenta) |
| `RESEND_API_KEY` | Opcional si usas Resend |
| `EMAIL_SMOKE_TEST_TO` | Destinatario del smoke real (`python apps/backend/scripts/email_smtp_smoke.py --send`) |
| `FRONTEND_BASE_URL` | Base URL del frontend para enlaces en correos (p. ej. `http://127.0.0.1:4200`) |
| `APP_PUBLIC_BASE_URL` | Alias legado de `FRONTEND_BASE_URL` |
| `YOUTUBE_API_KEY` | Opcional; contrato YouTube Data API / proveedores aprobados para resolución de audio |

Sin PocketBase, coloca Parquet en:

```
data/bronze/raw_spotify.parquet
```

(o deja que el bootstrap del pipeline lo genere desde PocketBase si está configurado).

---

## 4. Ejecutar ELT (obligatorio antes de la API / Compose)

**Pipeline canónico:**

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

**Importante:** con `RUN_ETL_ON_BOOT=never` (default en Compose), el contenedor **no** reconstruye el warehouse. En una instalación nueva: primero `make pipeline`, luego Compose o uvicorn.

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

### Cuentas demo (B2C + B2B) — seed opt-in

Estado y rutas de demostración: [STATUS.md](STATUS.md).

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

**Regalías (Spec 030 histórica):** `/royalties`, `/payouts` — fondos distribuibles + payout **simulado** (no banco real). Ver `.specify/history/030-royalties-settlements-and-simulated-payouts/`.

**Distribución artística (Spec 031 histórica):** `/artist/*`, `/catalog-review/*` — subir privado → revisar → publicar. Media en `data/media/`. Cuenta `demo.artist`. Ver `.specify/history/031-artist-music-submission-catalog-review-and-release-publishing/`.

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

Smoke contra la API real (requiere backend levantado; desde la raíz del repo):

```bash
python automation/scripts/smoke_api.py --base-url http://localhost:8000
python automation/scripts/smoke_user_journey.py --base-url http://localhost:8000
```

Playwright (`automation/playwright`) requiere `npm install` en esa carpeta; **no está instalado por defecto** en todos los entornos.

---

## 8. Docker (comando oficial)

Compose canónico en la **raíz** (`compose.yml`). Solo incluye `backend` y `frontend`. PocketBase y el pipeline ELT **no** son servicios de este Compose.

```bash
# 1) Preparar warehouse en el host (obligatorio en instalación nueva)
make pipeline

# 2) Levantar runtime
docker compose up --build
```

| Servicio | Puerto | Rol |
|----------|--------|-----|
| `backend` | `8000:8000` | FastAPI + DuckDB montado desde `./data` |
| `frontend` | `8080:80` | Nginx + SPA (proxy `/api`) |

- Logs: `docker compose logs -f backend`
- Parar: `docker compose down`
- `RUN_ETL_ON_BOOT` default = `never` → **no** reconstruye el warehouse al arrancar.
- Audio: usar `YOUTUBE_API_KEY` / proveedores aprobados según [architecture/playback.md](architecture/playback.md). No documentar herramientas no canónicas como sustituto del contrato.

Para otra máquina desde cero:

```bash
git clone <repo>
cd voxmetriks
cp infrastructure/environments/.env.example .env   # o copy en Windows
make pipeline
docker compose up --build
```

El warehouse DuckDB **no** se versiona (`.gitignore`); se genera con el pipeline. La caché de audio (`app_track_audio_source`) se llena al reproducir.

---

## Endpoints de referencia (API v1)

| Área | Ejemplos |
|------|----------|
| Identidad | `POST /api/v1/users/login`, `POST /api/v1/users/register`, `GET /api/v1/users/me` |
| Catálogo (streaming) | `GET /api/v1/catalog/artists`, `/genres`, `/tracks` |
| Artistas (negocio) | `GET/POST /api/v1/artists` (perfiles B2B; UI `/artist-profiles`) |
| Empresa (ejemplos) | `/organizations`, `/crm`, `/plans`, `/billing`, `/campaigns`, `/compliance`, `/platform-ops` |
| Biblioteca | `GET/POST /api/v1/playlists`, `GET/POST /api/v1/favorites/{id}` |
| Music search | `GET /api/v1/tracks/music-search`, adopt / repair-source |
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

Estado de cierre histórico: Spec 028 (con reporting 024 + CS/support 025). Documentación: [.specify/history/028-enterprise-integration-and-final-validation/](../.specify/history/028-enterprise-integration-and-final-validation/). Índice histórico: [.specify/history/README.md](../.specify/history/README.md).

Seed demo **explícito y opt-in** (marcado synthetic; no usar como producción):

```bash
cd apps/backend
# Windows PowerShell
$env:VOXMETRIKS_SEED_ENTERPRISE_DEMO="1"; python scripts/seed_enterprise_demo.py
# Linux / macOS
VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python scripts/seed_enterprise_demo.py
```

Detalle de estado vigente: [STATUS.md](STATUS.md).

Nota: rutas `/api/v1/artists` de negocio ≠ catálogo streaming (`/api/v1/catalog/artists`). UI empresarial de artistas: `/artist-profiles`.

---

## Documentación relacionada

- [README.md](../README.md) — visión y estructura del repo
- [.specify/history/README.md](../.specify/history/README.md) — índice histórico de Specs
- [docs/uml/README.md](uml/README.md) — diagramas PlantUML
- [STATUS.md](STATUS.md) — estado actual del producto
