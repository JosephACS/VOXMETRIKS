# ── Voxmetriks — Backend + ELT (Dockerfile canónico) ─────────────────────────
# Multi-stage, Python 3.12 slim. Sirve la API FastAPI y ejecuta el pipeline ELT.
# Usado por el Compose canónico de la raíz:
#
#   docker compose up --build
#
# Alternativa API-only: apps/backend/Dockerfile (no es el flujo oficial).

# ════════════════════════════════════════════════════════════════════════════
# Stage 1 — Dependencias
# ════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS deps

WORKDIR /build

# libstdc++6 requerida por los wheels de duckdb / pyarrow
RUN apt-get update \
 && apt-get install -y --no-install-recommends libstdc++6 \
 && rm -rf /var/lib/apt/lists/*

# backend/requirements.txt es el autoritativo (incluye bcrypt, uvicorn[standard])
COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ════════════════════════════════════════════════════════════════════════════
# Stage 2 — Runtime
# ════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends libstdc++6 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd -m -u 1000 voxmetrik

WORKDIR /app

# Paquetes instalados desde el stage deps
COPY --from=deps /usr/local/lib/python3.12/site-packages \
                 /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Código: backend (API) + elt (pipeline)
COPY --chown=voxmetrik:voxmetrik apps/backend/ ./backend/
COPY --chown=voxmetrik:voxmetrik analytics/elt/ ./elt/
COPY --chown=voxmetrik:voxmetrik infrastructure/environments/.env.example .env.example

# Directorios de datos ANTES del VOLUME (mkdir+chown sin efecto si va después)
RUN mkdir -p /app/data/warehouse /app/data/bronze /app/data/silver /app/data/gold \
 && chown -R voxmetrik:voxmetrik /app

VOLUME ["/app/data"]

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    DB_PATH=/app/data/warehouse/voxmetrik.duckdb \
    HOST=0.0.0.0 \
    PORT=8000

USER voxmetrik
EXPOSE 8000

# Por defecto levanta la API. El pipeline se invoca como servicio aparte en compose.
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
