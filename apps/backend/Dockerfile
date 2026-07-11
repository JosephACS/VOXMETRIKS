# VOXMETRIK_V2 — Backend Dockerfile
# Builds API-only image; full stack uses root Dockerfile + docker-compose.yml

FROM python:3.12-slim AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends libstdc++6 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd -m -u 1000 voxmetrik

WORKDIR /app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . ./

RUN mkdir -p /app/data/warehouse /app/data/bronze /app/data/silver /app/data/gold \
 && chown -R voxmetrik:voxmetrik /app

USER voxmetrik

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    DB_PATH=/app/data/warehouse/voxmetrik.duckdb \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
