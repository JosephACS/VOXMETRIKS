# Deployment — Despliegue

## Requisitos

| Componente | Mínimo |
|------------|--------|
| Python | 3.12 |
| Node.js | 20 LTS |
| Docker | 24+ (opcional) |
| RAM | 4 GB (8 GB recomendado con ETL) |
| Disco | 2 GB libres |

## Variables de entorno

Copiar plantilla a `.env` en raíz (`infrastructure/environments/.env.example`) y/o `apps/backend/.env`.

### Esenciales

```env
ENVIRONMENT=production
DB_PATH=/app/data/warehouse/voxmetrik.duckdb
SECRET_KEY=<generar-clave-segura>
CORS_ORIGINS=https://tu-dominio.com
HOST=0.0.0.0
PORT=8000
RUN_ETL_ON_BOOT=never
```

### Fuente ELT (opcional; fuera de Compose)

PocketBase u otras fuentes se configuran para el pipeline en el **host**, no como servicios del Compose canónico.

```env
POCKETBASE_URL=http://127.0.0.1:8090
POCKETBASE_EMAIL=admin@example.com
POCKETBASE_PASSWORD=***
```

### Logging

```env
LOG_JSON=true
LOG_TO_FILES=true
LOG_LEVEL=INFO
ENVIRONMENT=production   # desactiva /docs
```

Ver lista completa en `apps/backend/.env.example`.

## Docker Compose (canónico — aplicación)

Archivo: **`compose.yml` en la raíz del repo**. Servicios: `backend`, `frontend`.

```bash
# Instalación nueva: warehouse primero (Compose no ejecuta ELT con RUN_ETL_ON_BOOT=never)
make pipeline
docker compose up --build -d
```

| Servicio | Puerto | Rol |
|----------|--------|-----|
| `backend` | `8000:8000` | FastAPI + DuckDB montado desde `./data` |
| `frontend` | `8080:80` | nginx + SPA (proxy `/api`) |

### Comandos útiles

```bash
docker compose logs -f backend
docker compose down
make pipeline   # ELT en el host; no es servicio Compose de aplicación
```

No inventar servicios Compose `api`, `pipeline` o `pocketbase` en el stack de aplicación.

## Docker Compose Airflow (orquestación ELT — Spec 048)

Archivo: **`infrastructure/airflow/compose.yml`**. Separado del runtime de producto.

- Airflow 3.3.0 + Python 3.12, LocalExecutor, metadata en Postgres propio.
- UI por defecto: `http://localhost:8081`.
- DAG manual `voxmetriks_elt` (`schedule=None`); no dispara ELT al hacer `up`.
- Entorno académico/demo — **no** producción / HA / Celery / Redis.

```bash
make down            # liberar DuckDB (mantenimiento obligatorio)
make airflow-up
make airflow-trigger # o UI
make airflow-down
make up
```

Credenciales: copiar `infrastructure/airflow/.env.example` → `.env` (placeholders; no versionar secretos).

## Despliegue manual

### Backend

```bash
# Desde la raíz del repo
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r apps/backend/requirements.txt
python analytics/elt/pipelines/elt_pipeline.py
cd apps/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

> **Nota:** Cache in-process no es multi-worker safe. Usar `--workers 1` o Redis futuro.

### Frontend

```bash
cd apps/frontend
npm ci
ng build --configuration production
# Servir dist/ con nginx
```

### nginx (ejemplo)

```nginx
server {
    listen 80;
    root /var/www/voxmetrik/dist;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/enterprise
```

## Makefile

```bash
make up      # docker compose up --build
make down
make logs
make pipeline
make test
```

## Checklist de despliegue controlado

- [ ] `ENVIRONMENT` acorde al entorno
- [ ] `SECRET_KEY` único
- [ ] `CORS_ORIGINS` explícitos (no `*`)
- [ ] SMTP configurado (o desactivar registro público)
- [ ] Warehouse generado con `make pipeline` / `python analytics/elt/pipelines/elt_pipeline.py`
- [ ] Logs rotativos activos
- [ ] Backups de `voxmetrik.duckdb` programados (si aplica)
