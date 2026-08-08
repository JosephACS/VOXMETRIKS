# Arquitectura — VOXMETRIK_V2

## Visión general

VOXMETRIK_V2 es una plataforma de analítica musical tipo Spotify: frontend Angular, API FastAPI y warehouse analítico DuckDB con arquitectura Medallion (Bronze / Silver / Gold). El sistema separa claramente **experiencia de usuario**, **lógica de negocio**, **acceso a datos** y **capa analítica**.

## Diagrama de arquitectura general

```mermaid
flowchart TB
    subgraph Client["Cliente"]
        FE[Angular SPA]
    end

    subgraph API["FastAPI"]
        MW[Middleware<br/>CORS · Rate limit · Timing · Request-ID]
        R1[Enterprise /api/v1]
        R2[Modular /api/v2]
        R3[Legacy packages /api/v1]
    end

    subgraph BL["Capa de negocio"]
        SVC[Services]
        REPO[Repositories]
    end

    subgraph Data["Datos"]
        DUCK[(DuckDB Warehouse)]
        PB[(PocketBase — fuente ELT)]
    end

    FE -->|HTTPS REST| MW
    MW --> R1 & R2 & R3
    R1 & R2 & R3 --> SVC
    SVC --> REPO
    REPO --> DUCK
    PB -->|ELT Pipeline| DUCK
```

## Flujo de capas backend

```mermaid
flowchart LR
    HTTP[HTTP Request] --> Route[Router / Endpoint]
    Route --> Service[Service]
    Service --> Cache{Cache TTL?}
    Cache -->|miss| Repo[Repository]
    Cache -->|hit| Response[JSON Response]
    Repo --> DuckDB[(DuckDB)]
    DuckDB --> Repo
    Repo --> Service
    Service --> Response
```

## Arquitectura Medallion

```mermaid
flowchart TB
    DS[Dataset Spotify ~100k filas]
    RAW[Raw / Bronze<br/>raw_spotify · bronze_raw_tracks]
    SIL[Silver<br/>silver_tracks · silver_streams · silver_users]
    GOLD[Gold — Dimensional<br/>dim_* · fact_*]
    AGG[Aggregates<br/>agg_*]
    DASH[Dashboard & API]

    DS --> RAW --> SIL --> GOLD --> AGG --> DASH
```

## Flujo ETL

```mermaid
flowchart LR
    PB[PocketBase / Parquet] --> Extract[Extract]
    Extract --> Clean[Cleaning]
    Clean --> Transform[Transform]
    Transform --> DIM[Dimensions]
    DIM --> FACT[Facts]
    FACT --> AGG[Aggregations]
    AGG --> CACHE[Dashboard Cache]
```

## Motor de recomendaciones

```mermaid
flowchart LR
    U[Usuario] --> H[Historial / Contexto SQL]
    H --> P[Popularity Score]
    H --> E[Engagement Score]
    H --> C[Collaborative Filter]
    H --> T[Trending Boost]
    P & E & C & T --> R[Ranking ponderado]
    R --> API[GET /tracks/recommendations]
    API --> FE[Frontend Discover]
```

## Autenticación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Angular
    participant API as FastAPI
    participant DB as DuckDB

    U->>FE: Login (demo/demo123)
    FE->>API: POST /api/v1/users/login
    API->>DB: Validar app_user + app_session
    DB-->>API: Token Bearer
    API-->>FE: { token, user }
    FE->>FE: Guardar token (localStorage)
    FE->>API: GET /api/v1/playlists<br/>Authorization: Bearer
    API->>API: Validar sesión
    API-->>FE: Datos del usuario
```

## Superficies API

| Superficie | Prefijo | Propósito |
|------------|---------|-----------|
| Enterprise | `/api/v1` | Dashboard, analytics, top tracks, recomendaciones, user insights |
| Modular V2 | `/api/v2` | Servicios de dominio desacoplados (streaming, search, dashboard) |
| Legacy packages | `/api/v1` | Catálogo, auth, playlists, favoritos, stats, explorer |
| Health | `/health`, `/api/v1/health` | Estado del warehouse y ETL |

## Principios de diseño

1. **Single warehouse authority** — Un único DuckDB canónico en `data/warehouse/voxmetrik.duckdb`.
2. **ELT-before-API** — El warehouse se construye antes de servir analytics (P7).
3. **Package-by-domain** — Módulos por dominio (`streaming`, `analytics`, `users`).
4. **AGG over FACT** — Las consultas de dashboard leen tablas agregadas cuando existen.
5. **Thin routes, fat services** — Los endpoints delegan en servicios; SQL vive en repositorios.

## Decisiones arquitectónicas (ADR resumidas)

| Decisión | Alternativa descartada | Motivo |
|----------|------------------------|--------|
| DuckDB | PostgreSQL | Analítica embebida, cero ops, OLAP local |
| FastAPI | Django REST | Async, OpenAPI nativo, tipado Pydantic |
| Angular 21 | React | Enterprise SPA, lazy loading standalone |
| Medallion | Schema plano | Trazabilidad ETL, separación raw/clean/gold |
| Heurístico (no ML) | Modelo entrenado | Explicable, sin GPU, apto académico |

## Referencias

- [database.md](../database/database.md) — Catálogo de tablas
- [backend.md](../backend/backend.md) — Detalle de módulos Python
- [frontend.md](../frontend/frontend.md) — Rutas y componentes Angular
