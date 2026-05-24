# ── VOXMETRIK_V2 — Dockerfile ────────────────────────────────────────────────
# Multi-stage build — Python 3.12 slim, sin compilaciones desde fuente.
#
# Uso:
#   docker build -t voxmetrik_v2 .
#   docker compose up

# ════════════════════════════════════════════════════════════════════════════
# Stage 1 — Instalar dependencias
# ════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS deps

WORKDIR /build

# libstdc++6 necesaria para los wheels pre-built de pyarrow y duckdb
RUN apt-get update \
 && apt-get install -y --no-install-recommends libstdc++6 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt


# ════════════════════════════════════════════════════════════════════════════
# Stage 2 — Runtime image
# ════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS runtime

# libstdc++6 también requerida en runtime (duckdb/pyarrow la necesitan)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libstdc++6 \
 && rm -rf /var/lib/apt/lists/*

# Usuario no-root por seguridad
RUN useradd -m -u 1000 voxmetrik

WORKDIR /app

# ── Copiar paquetes instalados desde el stage deps ──────────────────────────
COPY --from=deps /usr/local/lib/python3.12/site-packages \
                 /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# ── Copiar código del proyecto ───────────────────────────────────────────────
COPY --chown=voxmetrik:voxmetrik requirements.txt  .
COPY --chown=voxmetrik:voxmetrik elt_pipeline.py   .
COPY --chown=voxmetrik:voxmetrik backend/          ./backend/
COPY --chown=voxmetrik:voxmetrik .env.example      .

# ── Crear directorios ANTES de declarar VOLUME ──────────────────────────────
# CRÍTICO: mkdir + chown debe ir ANTES de VOLUME.
# Si se hace después, Docker ya montó el volumen y el chown no tiene efecto.
RUN mkdir -p /app/duckdb /app/data/processed/stage \
 && chown -R voxmetrik:voxmetrik /app

# Declarar volúmenes DESPUÉS de mkdir+chown
VOLUME ["/app/duckdb", "/app/data"]

# ── Variables de entorno ─────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    DB_PATH=/app/duckdb/voxmetrik.duckdb \
    HOST=0.0.0.0 \
    PORT=8000

USER voxmetrik

EXPOSE 8000

# Comando por defecto: levantar la API
# El pipeline se ejecuta como servicio separado en docker-compose
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]