# Voxmetriks

Plataforma de analítica musical sobre dataset Spotify: SPA Angular + API FastAPI + warehouse DuckDB (arquitectura Medallion).

**Documentación canónica:** este README es el único punto de entrada. El arranque operativo está en [`docs/QUICKSTART.md`](docs/QUICKSTART.md).

---

## Qué es

| Capa | Tecnología | Ubicación |
|------|------------|-----------|
| Frontend | Angular 21 | `frontend/` |
| API | FastAPI 2.x | `backend/app/` |
| Warehouse | DuckDB (Gold + tablas app) | `data/warehouse/voxmetrik.duckdb` |
| ELT | Python (Bronze → Silver → Gold) | `elt/pipelines/elt_pipeline.py` |

| Specs SDD | Markdown 001–011 | `specs/` |

Principios de diseño: package-by-domain (P2), single warehouse authority (P4), ELT-before-API (P7). Ver [`.specify/memory/constitution.md`](.specify/memory/constitution.md). La entrega académica TGA07 (docx) está en el repo hermano [`../voxmetriks-entregas`](../voxmetriks-entregas).

---

## Inicio rápido

```bash
# Ver guía completa paso a paso
docs/QUICKSTART.md
```

Resumen mínimo (local):

1. `pip install -r requirements.txt` y `pip install -r backend/requirements.txt`
2. `cp .env.example .env`
3. `python elt/pipelines/elt_pipeline.py`
4. `cd backend && uvicorn app.main:app --reload`
5. `cd frontend && npm install && npm start` → http://localhost:4200

Credenciales demo (seed automático): `demo` / `demo123`. Engineer (pipeline/explorer): `admin` / `admin123`.

---

## Estructura del repositorio

```
voxmetriks/
├── frontend/              # SPA Angular (PKG-01..07)
├── backend/
│   ├── app/               # FastAPI — main.py, packages/
│   └── tests/             # pytest (health, login, playlists, favorites)
├── elt/                   # Extract / transform / pipelines
├── data/warehouse/        # DuckDB canónico (generado por ELT)
├── specs/                 # Specs operativas 001–011 + trazabilidad (SDD)
├── .specify/              # Spec Kit (constitución, plantillas, scripts)
├── docs/
│   ├── QUICKSTART.md      # ← guía única de arranque
│   └── uml/               # Diagramas PlantUML
├── docker-compose.yml     # pocketbase → pipeline → api → frontend
└── scripts/               # validate_warehouse.py, smoke tests
```

---

## API y salud

| Recurso | URL |
|---------|-----|
| Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| API v1 | http://localhost:8000/api/v1/… |

Prefijo REST: `/api/v1`. Autenticación: header `Authorization: Bearer <token>` (login en `/api/v1/users/login`).

---

## Specs y documentación

| Documento | Descripción |
|-----------|-------------|
| [`specs/README.md`](specs/README.md) | Índice specs 001–011 |
| [`specs/TRACEABILITY-MASTER.md`](specs/TRACEABILITY-MASTER.md) | Matriz CU→FR→Impl |
| [`docs/uml/`](docs/uml/) | Casos de uso, componentes, arquitectura, flujo ELT |
| [`../voxmetriks-entregas`](../voxmetriks-entregas) | Entrega académica TGA07 (docx) |

---

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Smoke contra el backend real:

```bash
uvicorn app.main:app --reload --port 8000
python ../scripts/smoke_api.py --base-url http://localhost:8000
python ../scripts/smoke_user_journey.py --base-url http://localhost:8000
```

La suite cubre health, login, logout real, RBAC engineer, explorer, protección de datos sensibles, búsqueda y limpieza de textos. `smoke_user_journey.py` agrega favoritos, playlists, recomendaciones e historial contra la API real.

---

## Docker

Una sola orden levanta todo (primera vez):

```bash
docker compose up --build
```

Orden de arranque: **pocketbase** (sirve el dataset ~100k desde `./pocketbase/pb_data`) → **pipeline** (corre el ELT y construye el DuckDB) → **api** (arranca al terminar el pipeline, P7) → **frontend** (nginx sirve la SPA y hace proxy `/api` → api).

### Arrancar en otra laptop/PC (desde cero)

Todo lo necesario viaja en git: código, `docker-compose.yml` y el dataset fuente (`pocketbase/pb_data`, ~20 MB). El warehouse DuckDB **no** se versiona (está en `.gitignore`); el pipeline lo reconstruye solo en el primer arranque. Tres pasos:

```bash
git clone <repo>
cd voxmetriks
cp .env.example .env          # Windows: copy .env.example .env  → completa credenciales PocketBase
docker compose up --build
```

Listo: frontend en http://localhost:8080, API en http://localhost:8000.

Notas:

- **`.env` no está en git** (lleva credenciales). Hay que crearlo desde `.env.example` en cada máquina.
- **`YOUTUBE_API_KEY` puede ir vacío:** la resolución de audio usa `yt-dlp` (sin cuota); la API de YouTube es solo respaldo.
- El **audio se resuelve solo al primer play** de cada canción (1–2 s) y queda cacheado en el DuckDB de esa máquina. La caché no viaja entre PCs; si quieres pre-calentarla corre `python scripts/resolve_audio_youtube.py --limit 2000` (opcional, con el backend apagado).

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:8080 |
| API / Swagger | http://localhost:8000/docs |
| PocketBase | http://localhost:8090 |

```bash
docker compose up -d pocketbase api frontend   # sin re-correr el pipeline
docker compose run --rm pipeline               # re-ejecutar el ELT
```

> El primer arranque requiere que `./pocketbase/pb_data` tenga el dataset y el superusuario, y que `.env` tenga las credenciales de PocketBase.

---

## Cuentas, verificación por correo y Google

- **Las cuentas son únicas:** el registro valida que el correo y el usuario no existan, y cada usuario tiene sus propios favoritos y playlists (`user_id`). El **nombre de usuario** es el que se muestra en el perfil.
- **Registro con código:** al crear una cuenta se envía un **código de 6 dígitos** al correo. Hay que ingresarlo para activar la cuenta e iniciar sesión.
  - Configura SMTP en `.env` (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`). Con Gmail usa una [contraseña de aplicación](https://myaccount.google.com/apppasswords).
  - **Sin SMTP (modo desarrollo):** no se envía correo; el código se imprime en el log del backend y se devuelve en la respuesta para probar en localhost.
- **Iniciar sesión con Google:** crea un **OAuth Client ID** (tipo *Web*) en [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials), agrega `http://localhost:4200` (y tu dominio) como *Authorized JavaScript origins*, y pega el ID en `GOOGLE_CLIENT_ID` del `.env`. Si está vacío, el botón de Google no aparece.

---

## Licencia

Proyecto académico Voxmetriks — uso según indicaciones del curso o cliente.
