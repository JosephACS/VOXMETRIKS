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

Copiar `.env.example` → `.env` en raíz y `apps/backend/.env`.

### Esenciales

```env
ENVIRONMENT=production
DB_PATH=/app/data/warehouse/voxmetrik.duckdb
SECRET_KEY=<generar-clave-segura>
CORS_ORIGINS=https://tu-dominio.com
HOST=0.0.0.0
PORT=8000
```

### PocketBase (ELT)

```env
POCKETBASE_URL=http://pocketbase:8090
POCKETBASE_EMAIL=admin@example.com
POCKETBASE_PASSWORD=***
```

### Logging producción

```env
LOG_JSON=true
LOG_TO_FILES=true
LOG_LEVEL=INFO
ENVIRONMENT=production   # desactiva /docs
```

Ver lista completa en `apps/backend/.env.example`.

## Docker Compose (recomendado)

```bash
docker compose -f infrastructure/docker/docker-compose.yml up --build -d
```

| Servicio | Puerto | Rol |
|----------|--------|-----|
| pocketbase | 8090 | Dataset fuente |
| pipeline | — | ELT one-shot |
| api | 8000 | FastAPI |
| frontend | 8080 | nginx + SPA |

Orden: pocketbase → pipeline → api → frontend.

### Comandos útiles

```bash
docker compose -f infrastructure/docker/infrastructure/docker/docker-compose.yml logs -f api
docker compose run --rm pipeline      # re-ETL
docker compose -f infrastructure/docker/docker-compose.yml up -d pocketbase api frontend  # sin pipeline
docker compose -f infrastructure/docker/infrastructure/docker/docker-compose.yml down
```

## Despliegue manual

### Backend

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ../elt/pipelines/elt_pipeline.py
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
make up      # docker compose -f infrastructure/docker/docker-compose.yml up --build
make down
make logs
make etl
make test
```

## Checklist producción

- [ ] `ENVIRONMENT=production`
- [ ] `SECRET_KEY` único
- [ ] `CORS_ORIGINS` explícitos (no `*`)
- [ ] SMTP configurado (o desactivar registro público)
- [ ] Warehouse generado y validado
- [ ] Logs rotativos activos
- [ ] Backups de `voxmetrik.duckdb` programados
