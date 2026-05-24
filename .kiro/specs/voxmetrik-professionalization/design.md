# Design Document: VOXMETRIK_V2 Architecture

## 1. System Overview

VOXMETRIK_V2 is a music analytics platform that processes Spotify dataset information through an ELT pipeline and exposes analytics via a RESTful API. The system uses DuckDB as an analytical warehouse, FastAPI for the API layer, and Docker for containerized deployment.

**Architecture Pattern**: ELT (Extract, Load, Transform) with read-only API layer  
**Deployment Model**: Containerized microservices (pipeline job + API service)  
**Data Flow**: PocketBase/Parquet → DuckDB → FastAPI → Clients

---

## 2. High-Level Architecture

```
┌─────────────────┐
│  Data Sources   │
│  - PocketBase   │
│  - Parquet      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ELT Pipeline   │
│  (elt_pipeline) │
│  - Extract      │
│  - Load         │
│  - Transform    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DuckDB       │
│   Warehouse     │
│  - Dimensions   │
│  - Facts        │
│  - Aggregations │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  Backend        │
│  - Routes       │
│  - Services     │
│  - Schemas      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Clients      │
│  - Frontend     │
│  - External API │
└─────────────────┘
```

---

## 3. Backend Architecture

### 3.1 Directory Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management (pydantic-settings)
├── database.py          # DuckDB connection management
├── logger.py            # Logging configuration
├── utils.py             # Utility functions
├── routes/              # API route handlers
│   ├── __init__.py
│   ├── artists.py       # Artist endpoints
│   ├── genres.py        # Genre endpoints
│   ├── tracks.py        # Track endpoints
│   └── stats.py         # Statistics endpoints
├── services/            # Business logic layer
│   ├── __init__.py
│   ├── base_service.py  # Generic query helpers
│   ├── artist_service.py
│   ├── genre_service.py
│   ├── track_service.py
│   └── stats_service.py
├── schemas/             # Pydantic models
│   ├── __init__.py
│   └── models.py        # Response models
└── tests/               # Test suite
    ├── __init__.py
    └── test_api.py
```

### 3.2 Layered Architecture

**Layer 1: API Routes** (`routes/`)
- Handle HTTP requests/responses
- Input validation via Pydantic
- Dependency injection for database connections
- Error handling and status codes

**Layer 2: Services** (`services/`)
- Business logic and data access
- Query construction and execution
- Data transformation
- Reusable across multiple routes

**Layer 3: Database** (`database.py`)
- DuckDB connection management (thread-local, read-only)
- Schema introspection
- Safe query execution
- Connection pooling

**Layer 4: Schemas** (`schemas/`)
- Pydantic v2 models for request/response validation
- Type safety and serialization
- OpenAPI documentation generation

---

## 4. FastAPI Application

### 4.1 Application Initialization

**File**: `backend/main.py`

```python
app = FastAPI(
    title="VOXMETRIK_V2 API",
    version="2.0.0",
    lifespan=lifespan,      # Startup/shutdown hooks
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc"       # ReDoc
)
```

**Lifespan Management**:
- Validates DuckDB database exists on startup
- Logs table count and database status
- Graceful shutdown handling

**Middleware**:
- CORS: Configurable origins (currently `*` for development)
- Methods: GET only (read-only API)

**Global Exception Handlers**:
- `ValueError` → 400 Bad Request
- `FileNotFoundError` → 503 Service Unavailable
- `Exception` → 500 Internal Server Error

### 4.2 API Endpoints

**Root Endpoints**:
- `GET /` - API metadata
- `GET /health` - Health check with database status

**Artists** (`/api/v1/artists`):
- `GET /artists` - List artists (paginated, searchable)
- `GET /artists/top` - Top artists by popularity
- `GET /artists/{artist_id}` - Get artist by ID
- `GET /artists/{artist_id}/stats` - Artist statistics

**Genres** (`/api/v1/genres`):
- `GET /genres` - List genres (paginated, searchable)
- `GET /genres/stats` - Genre statistics
- `GET /genres/{genre_id}` - Get genre by ID

**Tracks** (`/api/v1/tracks`):
- `GET /tracks` - List tracks (paginated, filterable)
- `GET /tracks/{track_id}` - Get track by ID
- `GET /tracks/{track_id}/features` - Audio features

**Statistics** (`/api/v1/stats`):
- `GET /stats/summary` - Warehouse summary counts
- `GET /stats/energia` - Energy distribution
- `GET /stats/top-tracks` - Top tracks by popularity
- `GET /stats/loads` - Pipeline execution history

### 4.3 Dependency Injection

**Database Connection**:
```python
def get_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    # Thread-local read-only connection
    # Automatic error recovery
    # Yields connection to route handlers
```

**Usage in Routes**:
```python
@router.get("/artists")
def list_artists(
    conn: duckdb.DuckDBPyConnection = Depends(get_conn)
):
    # Use conn for queries
```

---

## 5. DuckDB Data Warehouse

### 5.1 Schema Design

**Dimensional Model** (Star Schema):

**Control Tables**:
- `ctl_carga_dataset` - Pipeline execution tracking
- `ctl_auditoria` - Audit log
- `ctl_reporte` - Report metadata

**Staging**:
- `raw_spotify` - Raw ingested data

**Dimensions**:
- `dim_artista` - Artists (id_artista, nombre_artista)
- `dim_genero` - Genres (id_genero, nombre_genero)
- `dim_album` - Albums (id_album, nombre_album, id_artista)
- `dim_track` - Tracks (id_track, spotify_track_id, nombre_track, ...)

**Facts**:
- `fact_audio_features` - Audio metrics per track

**Aggregations** (Pre-computed):
- `agg_top_artistas` - Artist popularity rankings
- `agg_genero_popularidad` - Genre statistics
- `agg_distribucion_energia` - Energy distribution buckets

### 5.2 Connection Management

**Thread-Local Connections**:
- Each FastAPI worker thread maintains its own DuckDB connection
- Read-only mode for API safety
- Connections persist for worker lifetime

**Error Recovery**:
- Automatic detection of serialization/version errors
- Graceful error messages directing to pipeline re-run
- Connection reset on errors

**Schema Introspection**:
- `get_table_columns()` - Returns actual column names from DESCRIBE
- `table_exists()` - Checks table existence
- `safe_query()` - Validates columns before SELECT

---

## 6. ELT Pipeline

### 6.1 Pipeline Flow

**File**: `elt_pipeline.py`

```
Extract → Load → Transform → Control
```

**Phase 1: Extract**
1. Try PocketBase authentication (superuser → user fallback)
2. Download most recent CSV from PocketBase collection
3. Fallback to local Parquet file if PocketBase unavailable
4. Parse CSV/Parquet into Pandas DataFrame

**Phase 2: Load**
1. Normalize column names (lowercase, map variants)
2. Clean null values and whitespace
3. Coerce data types (float, int, bool)
4. Deduplicate on track_id
5. Insert into `raw_spotify` staging table

**Phase 3: Transform**
1. Populate dimensions (dim_artista, dim_genero, dim_album, dim_track)
2. Populate fact table (fact_audio_features)
3. Generate aggregations (agg_*)
4. All transforms use COALESCE/NULLIF for null safety

**Phase 4: Control**
1. Record execution metadata in `ctl_carga_dataset`
2. Log row counts and execution time

### 6.2 Data Normalization

**Column Mapping**:
- Handles variant column names (e.g., `name` → `track_name`)
- Adds missing columns with defaults
- Preserves only schema-defined columns

**Type Coercion**:
- Float columns: `danceability`, `energy`, `loudness`, etc.
- Integer columns: `popularity`, `duration_ms`, `key_col`, etc.
- Boolean: `explicit`

**Data Cleaning**:
- Strip whitespace from strings
- Replace empty strings with NULL
- Drop rows with null `track_name` (NOT NULL constraint)

### 6.3 Error Handling

**DuckDB Corruption Recovery**:
- Detects serialization/version errors
- Backs up corrupt database with timestamp
- Recreates database from scratch
- Automatic retry on first failure

**PocketBase Retry Logic**:
- Exponential backoff (3 retries, 2s delay)
- Graceful fallback to Parquet
- Detailed error logging

---

## 7. Docker Architecture

### 7.1 Multi-Stage Dockerfile

**Stage 1: deps** (Build dependencies)
```dockerfile
FROM python:3.12-slim AS deps
# Install libstdc++6 for pyarrow/duckdb
# Install Python dependencies
```

**Stage 2: runtime** (Production image)
```dockerfile
FROM python:3.12-slim AS runtime
# Copy installed packages from deps stage
# Create non-root user (voxmetrik)
# Copy application code
# Set up volumes and environment
```

**Image Characteristics**:
- Base: `python:3.12-slim`
- Non-root user: `voxmetrik` (UID 1000)
- Prebuilt wheels only (no compilation)
- Minimal dependencies (libstdc++6)

### 7.2 Docker Compose Services

**Service: pipeline**
- **Purpose**: One-time ELT job
- **Command**: `python elt_pipeline.py`
- **Restart**: `no` (exits after completion)
- **Volumes**: `duckdb_data`, `parquet_data`
- **Exit Code**: 0 = success, 1 = failure

**Service: api**
- **Purpose**: FastAPI backend
- **Command**: `uvicorn backend.main:app --workers 2`
- **Restart**: `unless-stopped`
- **Ports**: `8000:8000`
- **Depends On**: `pipeline` (service_completed_successfully)
- **Volumes**: `duckdb_data` (read-only access)
- **Health Check**: HTTP GET `/health` every 30s

**Service: pocketbase**
- **Purpose**: Data source (optional)
- **Image**: `spectado/pocketbase:latest`
- **Ports**: `8090:8090`
- **Volumes**: `pb_data`
- **Health Check**: HTTP GET `/api/health`

### 7.3 Volumes

**duckdb_data**:
- Shared between pipeline (write) and api (read)
- Persists DuckDB warehouse across restarts

**parquet_data**:
- Used by pipeline for Parquet fallback
- Not accessed by API

**pb_data**:
- PocketBase persistent storage
- Independent from main application

### 7.4 Networking

**Network**: `voxmetrik` (bridge driver)
- Internal communication between services
- Isolated from host network
- Services resolve by name (e.g., `http://pocketbase:8090`)

---

## 8. Configuration Management

### 8.1 Environment Variables

**File**: `backend/config.py`

**DuckDB**:
- `DB_PATH` - Database file path (default: `duckdb/voxmetrik.duckdb`)

**PocketBase**:
- `POCKETBASE_URL` - PocketBase server URL (default: `http://127.0.0.1:8090`)
- `POCKETBASE_EMAIL` - Authentication email
- `POCKETBASE_PASSWORD` - Authentication password
- `PB_COLLECTION` - Collection name (default: `datasets`)

**Server**:
- `HOST` - Bind address (default: `0.0.0.0`)
- `PORT` - Listen port (default: `8000`)
- `RELOAD` - Auto-reload on code changes (default: `False`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

**Pipeline**:
- `MAX_RETRIES` - PocketBase retry attempts (default: `3`)
- `RETRY_DELAY_S` - Retry delay in seconds (default: `2`)

### 8.2 Settings Management

**Pydantic Settings**:
- Loads from `.env` file (backend/ or project root)
- Type validation and coercion
- Cached singleton pattern (`@lru_cache`)
- Case-insensitive environment variables

---

## 9. PocketBase Integration

### 9.1 Authentication Flow

**Dual Endpoint Strategy**:
1. Try `/api/collections/_superusers/auth-with-password` (PocketBase ≥ 0.23)
2. Fallback to `/api/collections/users/auth-with-password` (older versions)

**Credentials**:
- Identity: `POCKETBASE_EMAIL`
- Password: `POCKETBASE_PASSWORD`
- Token stored in client instance

### 9.2 Data Extraction

**Record Retrieval**:
- Fetch most recent record from `datasets` collection
- Sort by `-created` (newest first)
- Limit: 1 record per request

**File Download**:
- Detect CSV file field in record
- Download via `/api/files/{collection}/{record_id}/{filename}`
- Parse CSV into Pandas DataFrame

**Fallback Mechanism**:
- If PocketBase unavailable → use local Parquet
- If both fail → raise RuntimeError with clear message

---

## 10. Logging and Observability

### 10.1 Logging Configuration

**Format**:
```
[YYYY-MM-DD HH:MM:SS] [LEVEL    ] logger_name — message
```

**Loggers**:
- `voxmetrik.api` - FastAPI application
- `voxmetrik.database` - Database operations
- `voxmetrik.pipeline` - ELT pipeline
- `voxmetrik.service` - Service layer

**Levels**:
- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages (non-critical issues)
- `ERROR` - Error messages (failures)

### 10.2 Health Monitoring

**Health Endpoint** (`GET /health`):
- Status: `ok`, `degraded`, `error`
- Database path
- Table count
- DuckDB version

**Docker Health Checks**:
- API: HTTP GET `/health` every 30s
- PocketBase: HTTP GET `/api/health` every 30s
- Start period: 10-15s
- Retries: 3

---

## 11. Deployment Strategy

### 11.1 Local Development

**Prerequisites**:
- Python 3.12
- Docker + Docker Compose
- `.env` file with configuration

**Steps**:
1. `docker compose up --build` - First-time setup
2. Pipeline runs automatically
3. API starts after pipeline completes
4. Access API at `http://localhost:8000/docs`

**Development Mode**:
```bash
cd backend
uvicorn main:app --reload
```

### 11.2 Production Deployment

**Cloud-Agnostic Approach**:
- Docker images compatible with AWS ECS, GCP Cloud Run, Azure Container Instances
- No vendor-specific dependencies
- Environment-based configuration

**Deployment Steps**:
1. Build Docker image: `docker build -t voxmetrik_v2 .`
2. Push to container registry
3. Deploy pipeline as one-time job
4. Deploy API as long-running service
5. Configure environment variables
6. Set up volume persistence for DuckDB

**Scaling Considerations**:
- API: Horizontal scaling (multiple workers/containers)
- DuckDB: Single-writer, multiple-reader (read-only API connections)
- Pipeline: Run as scheduled job (cron/CloudWatch Events)

### 11.3 CI/CD Pipeline (Planned)

**CI (Continuous Integration)**:
- Automated tests on pull requests
- Linting: flake8, black, mypy
- Docker image build validation
- Test coverage reporting

**CD (Continuous Deployment)**: Out of scope
- Manual deployment preferred initially
- Future: GitOps with ArgoCD/Flux

---

## 12. Security Considerations

### 12.1 Current Security Measures

**Container Security**:
- Non-root user execution (`voxmetrik:1000`)
- Minimal base image (`python:3.12-slim`)
- No unnecessary packages

**API Security**:
- Read-only database connections
- Input validation via Pydantic
- Parameterized queries (SQL injection prevention)
- CORS restrictions (configurable)

**Secrets Management**:
- Environment variables for credentials
- No hardcoded secrets in code
- `.env` file excluded from version control

### 12.2 Future Enhancements

**Authentication/Authorization**:
- JWT tokens for API access
- Role-based access control (RBAC)
- API key management

**Network Security**:
- HTTPS/TLS termination
- Rate limiting
- IP whitelisting

---

## 13. Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Backend Framework** | FastAPI | 0.111.0 | REST API |
| **Web Server** | Uvicorn | 0.30.1 | ASGI server |
| **Database** | DuckDB | 1.1.3 | Analytical warehouse |
| **Data Processing** | Pandas | 2.2.2 | ELT transformations |
| **Data Format** | PyArrow | 16.1.0 | Parquet support |
| **Validation** | Pydantic | 2.7.4 | Schema validation |
| **HTTP Client** | httpx | 0.27.0 | PocketBase integration |
| **Configuration** | python-dotenv | 1.0.1 | Environment management |
| **Logging** | python-json-logger | 2.0.7 | Structured logging |
| **Containerization** | Docker | - | Deployment |
| **Orchestration** | Docker Compose | 3.9 | Multi-service management |
| **Data Source** | PocketBase | latest | CSV storage |

---

## 14. Design Principles

### 14.1 Architectural Principles

**Separation of Concerns**:
- Routes handle HTTP, services handle logic, database handles data
- Clear boundaries between layers

**Read-Only API**:
- API never writes to DuckDB
- All writes happen via pipeline
- Prevents data corruption

**Fail-Safe Defaults**:
- Graceful degradation (PocketBase → Parquet fallback)
- Automatic error recovery (DuckDB corruption)
- Comprehensive error messages

**Schema-Driven Development**:
- All queries validated against live schema
- No invented columns
- Type safety via Pydantic

### 14.2 Code Quality Standards

**Type Safety**:
- Type hints on all function signatures
- Pydantic models for data validation
- MyPy compatibility

**Documentation**:
- Docstrings on all modules and functions
- OpenAPI documentation auto-generated
- Inline comments for complex logic

**Error Handling**:
- Specific exception types
- Contextual error messages
- Logging at appropriate levels

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-16  
**Status**: Draft
