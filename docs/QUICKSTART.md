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

Sin PocketBase, coloca Parquet en:

```
data/bronze/raw_spotify.parquet
```

(o deja que el bootstrap del pipeline lo genere desde PocketBase).

---

## 4. Ejecutar ELT (obligatorio antes de la API)

```bash
python analytics/elt/pipelines/elt_pipeline.py
```

Crea o actualiza `data/warehouse/voxmetrik.duckdb` con capas Medallion (`dim_*`, `fact_*`, `agg_*`, `ctl_*`).

Validación opcional post-ELT:

```bash
python automation/scripts/validate_warehouse.py
```

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

---

## 7. Tests y smoke (opcional)

```bash
cd apps/backend
pytest tests/ -v
```

Smoke contra la API real (requiere backend levantado):

```bash
python ../automation/scripts/smoke_api.py --base-url http://localhost:8000
python ../automation/scripts/smoke_user_journey.py --base-url http://localhost:8000
```

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
| Catálogo | `GET /api/v1/artists`, `/genres`, `/tracks` |
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

Actualiza `frontend/src/environments/environment.ts` → `apiUrl`.

### Frontend no conecta a API

Confirma `CORS_ORIGINS` e incluye `http://localhost:4200`. Verifica también que `apiUrl` apunte a `http://localhost:8000/api/v1`.

---

## Documentación relacionada

- [README.md](../README.md) — visión y estructura del repo  
- [automation/specs/README.md](../README.md) — índice de specs SDD  
- [docs/uml/README.md](../README.md) — diagramas PlantUML  
- [../voxmetriks-entregas](../voxmetriks-entregas) — entrega académica TGA07 (docx)
