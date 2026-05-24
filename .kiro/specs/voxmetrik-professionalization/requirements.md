# Requirements Document: VOXMETRIK_V2 Professionalization

## 1. Introduction

### 1.1 Project Overview

VOXMETRIK_V2 is an existing, functional music analytics platform that processes Spotify dataset information through an ELT (Extract, Load, Transform) pipeline and exposes the data via a RESTful API. The system is built on a modern Python stack with FastAPI, DuckDB as an analytical warehouse, and containerized deployment using Docker.

**Current Status**: The project has a working backend with API endpoints, a functional ELT pipeline, Docker containerization, and PocketBase integration for data ingestion.

**Project Goal**: Professionalize the existing codebase without recreating it from scratch. The focus is on improving documentation, stabilizing infrastructure, preparing for frontend integration, and establishing deployment and observability practices.

### 1.2 Scope

This specification covers improvements and additions to the existing VOXMETRIK_V2 system:

**In Scope**:
- Backend API professionalization and OpenAPI documentation enhancement
- Docker infrastructure stabilization
- Frontend preparation (Angular integration planning)
- Cloud deployment readiness (cloud-agnostic approach)
- CI/CD pipeline implementation (CI only: tests + linting)
- Observability and logging improvements
- Essential testing for critical paths

**Out of Scope**:
- Complete backend rewrite or architecture replacement
- Changing the core technology stack (FastAPI, DuckDB, Docker)
- Modifying existing SQL queries or database schema
- Recreating the ELT pipeline from scratch
- Full deployment automation (CD)

### 1.3 Stakeholders

- **Development Team**: Responsible for implementing improvements
- **End Users**: Will consume analytics data through the API and future frontend
- **DevOps/Infrastructure**: Responsible for deployment and monitoring

---

## 2. Current System Architecture

### 2.1 Technology Stack

**Backend**:
- **Framework**: FastAPI 0.111.0
- **Runtime**: Python 3.12
- **Web Server**: Uvicorn 0.30.1 with standard extras
- **Database**: DuckDB 1.1.3 (analytical warehouse)
- **Data Processing**: Pandas 2.2.2, PyArrow 16.1.0
- **HTTP Client**: httpx 0.27.0 (PocketBase integration)
- **Configuration**: Pydantic 2.7.4, pydantic-settings 2.3.4, python-dotenv 1.0.1
- **Logging**: python-json-logger 2.0.7

**Infrastructure**:
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose 3.9
- **Base Image**: python:3.12-slim
- **Data Storage**: PocketBase 8090 (optional data source)

**Data Sources**:
- PocketBase CSV uploads (primary)
- Local Parquet files (fallback)

### 2.2 Current Database Schema

The DuckDB warehouse implements a dimensional model with the following tables:

**Control Tables**:
- `ctl_carga_dataset`: Pipeline execution tracking
- `ctl_auditoria`: Audit log for data operations
- `ctl_reporte`: Report generation metadata

**Staging**:
- `raw_spotify`: Raw ingested data from CSV/Parquet sources

**Dimensions**:
- `dim_artista`: Artist master data (id_artista, nombre_artista)
- `dim_genero`: Genre master data (id_genero, nombre_genero)
- `dim_album`: Album master data (id_album, nombre_album, id_artista)
- `dim_track`: Track master data with foreign keys to artist, album, genre

**Facts**:
- `fact_audio_features`: Audio feature metrics per track (popularity, danceability, energy, loudness, speechiness, acousticness, instrumentalness, liveness, valence, tempo, key, mode, time_signature)

**Aggregations**:
- `agg_top_artistas`: Pre-aggregated artist statistics
- `agg_genero_popularidad`: Genre-level popularity and energy metrics
- `agg_distribucion_energia`: Energy distribution buckets with popularity and danceability

### 2.3 Existing API Endpoints

**Root Endpoints**:
- `GET /` - API metadata and navigation
- `GET /health` - Health check with database status

**Artists** (`/api/v1/artists`):
- `GET /api/v1/artists` - List artists (paginated, searchable)
- `GET /api/v1/artists/top` - Top artists by average popularity
- `GET /api/v1/artists/{artist_id}` - Get artist by ID
- `GET /api/v1/artists/{artist_id}/stats` - Artist statistics

**Genres** (`/api/v1/genres`):
- `GET /api/v1/genres` - List genres (paginated, searchable)
- `GET /api/v1/genres/stats` - Genre statistics with popularity and energy
- `GET /api/v1/genres/{genre_id}` - Get genre by ID

**Tracks** (`/api/v1/tracks`):
- `GET /api/v1/tracks` - List tracks (paginated, filterable by search, genre_id, artist_id)
- `GET /api/v1/tracks/{track_id}` - Get track by ID
- `GET /api/v1/tracks/{track_id}/features` - Track audio features

**Statistics** (`/api/v1/stats`):
- `GET /api/v1/stats/summary` - High-level warehouse counts
- `GET /api/v1/stats/energia` - Energy distribution
- `GET /api/v1/stats/top-tracks` - Top tracks by popularity
- `GET /api/v1/stats/loads` - Recent pipeline load history

### 2.4 ELT Pipeline

**Extract Phase**:
- Attempts PocketBase authentication (superuser endpoint with fallback to user endpoint)
- Downloads most recent CSV from PocketBase collection
- Falls back to local Parquet file if PocketBase unavailable

**Load Phase**:
- Normalizes column names and data types
- Cleans null values and whitespace
- Deduplicates on track_id
- Inserts into `raw_spotify` staging table

**Transform Phase**:
- Populates dimension tables (dim_artista, dim_genero, dim_album, dim_track)
- Populates fact table (fact_audio_features)
- Generates aggregation tables (agg_top_artistas, agg_genero_popularidad, agg_distribucion_energia)

**Error Handling**:
- DuckDB serialization error recovery (automatic database recreation)
- Retry logic with exponential backoff for PocketBase operations
- Comprehensive logging at each phase

### 2.5 Docker Architecture

**Multi-Stage Dockerfile**:
- Stage 1 (`deps`): Installs Python dependencies with prebuilt wheels
- Stage 2 (`runtime`): Minimal runtime image with non-root user

**Docker Compose Services**:
- `pipeline`: One-time ELT job (exits after completion)
- `api`: FastAPI service (depends on pipeline completion)
- `pocketbase`: Optional data source service

**Volumes**:
- `duckdb_data`: Shared DuckDB database (pipeline writes, API reads)
- `parquet_data`: Local Parquet fallback data
- `pb_data`: PocketBase persistent storage

**Networking**:
- Internal bridge network (`voxmetrik`)
- Exposed ports: 8000 (API), 8090 (PocketBase)

---

## 3. Functional Requirements

### FR-1: Backend API Professionalization

**FR-1.1**: The API SHALL maintain all existing endpoints without breaking changes.

**FR-1.2**: The API SHALL provide comprehensive OpenAPI documentation including:
- Detailed endpoint descriptions
- Request/response examples
- Error response schemas
- Authentication requirements (if added)

**FR-1.3**: The API SHALL implement consistent error handling with:
- Standardized error response format
- Appropriate HTTP status codes
- Descriptive error messages

**FR-1.4**: The API SHALL support CORS configuration for frontend integration with environment-based origin whitelisting.

### FR-2: Data Pipeline Stability

**FR-2.1**: The ELT pipeline SHALL continue to support both PocketBase and Parquet data sources.

**FR-2.2**: The pipeline SHALL maintain automatic DuckDB corruption recovery.

**FR-2.3**: The pipeline SHALL log all extraction, load, and transform operations with timestamps and row counts.

**FR-2.4**: The pipeline SHALL record execution metadata in `ctl_carga_dataset` table.

### FR-3: Frontend Integration Preparation

**FR-3.1**: The API SHALL expose metadata endpoints for frontend discovery:
- Available filters and dimensions
- Data freshness indicators
- Schema version information

**FR-3.2**: The API SHALL support query parameters for:
- Pagination (page, limit)
- Filtering (search, genre_id, artist_id)
- Sorting (order_by, direction)

**FR-3.3**: The API SHALL return consistent paginated response format across all list endpoints.

### FR-4: Health Monitoring

**FR-4.1**: The `/health` endpoint SHALL return:
- Service status (ok, degraded, error)
- Database connection status
- Available tables count
- DuckDB version

**FR-4.2**: The health check SHALL be compatible with Docker healthcheck probes.

**FR-4.3**: The API SHALL expose a `/metrics` endpoint for observability (optional, future enhancement).

---

## 4. Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1**: API endpoints SHALL respond within 500ms for queries returning up to 500 records.

**NFR-1.2**: The ELT pipeline SHALL process up to 100,000 records within 5 minutes.

**NFR-1.3**: The API SHALL support at least 2 concurrent workers in production.

### NFR-2: Reliability

**NFR-2.1**: The API SHALL achieve 99% uptime in production environments.

**NFR-2.2**: The system SHALL automatically recover from DuckDB serialization errors without manual intervention.

**NFR-2.3**: The pipeline SHALL retry transient PocketBase connection failures up to 3 times with exponential backoff.

### NFR-3: Maintainability

**NFR-3.1**: All Python code SHALL follow PEP 8 style guidelines.

**NFR-3.2**: All modules SHALL include docstrings describing purpose and usage.

**NFR-3.3**: The codebase SHALL maintain type hints for function signatures.

**NFR-3.4**: Configuration SHALL be externalized via environment variables (no hardcoded credentials).

### NFR-4: Scalability

**NFR-4.1**: The system SHALL support horizontal scaling of API workers.

**NFR-4.2**: The DuckDB database SHALL support datasets up to 10 million records.

**NFR-4.3**: The Docker setup SHALL be compatible with Kubernetes deployment.

### NFR-5: Security

**NFR-5.1**: The API SHALL run as a non-root user in containers.

**NFR-5.2**: Sensitive configuration (PocketBase credentials) SHALL be stored in environment variables or secrets management.

**NFR-5.3**: The API SHALL validate all input parameters to prevent injection attacks.

**NFR-5.4**: CORS SHALL be configurable to restrict allowed origins in production.

### NFR-6: Observability

**NFR-6.1**: All services SHALL log to stdout in structured format (JSON).

**NFR-6.2**: Logs SHALL include:
- Timestamp
- Log level (DEBUG, INFO, WARNING, ERROR)
- Module name
- Message

**NFR-6.3**: The API SHALL log all incoming requests with:
- HTTP method
- Path
- Status code
- Response time

**NFR-6.4**: The pipeline SHALL log execution summary including:
- Start/end timestamps
- Records processed
- Errors encountered

### NFR-7: Testability

**NFR-7.1**: Critical API endpoints SHALL have automated tests covering:
- Successful responses
- Error conditions
- Input validation

**NFR-7.2**: The pipeline SHALL have tests for:
- Data normalization logic
- Error recovery mechanisms
- Schema validation

**NFR-7.3**: Tests SHALL be executable via `pytest` command.

**NFR-7.4**: Test coverage SHALL be measurable via coverage reports.

### NFR-8: Deployment

**NFR-8.1**: The system SHALL be deployable via `docker compose up` command.

**NFR-8.2**: The Docker images SHALL be cloud-agnostic (compatible with AWS ECS, GCP Cloud Run, Azure Container Instances).

**NFR-8.3**: The system SHALL support environment-based configuration for dev/staging/production.

**NFR-8.4**: Database volumes SHALL persist across container restarts.

---

## 5. Technical Objectives

### TO-1: OpenAPI Documentation Enhancement

**Objective**: Improve API documentation to professional standards for frontend developers and external consumers.

**Success Criteria**:
- All endpoints have detailed descriptions
- Request/response schemas are complete with examples
- Interactive Swagger UI is fully functional
- ReDoc alternative documentation is available

### TO-2: Docker Infrastructure Stabilization

**Objective**: Ensure Docker setup is production-ready and follows best practices.

**Success Criteria**:
- Multi-stage builds minimize image size
- Non-root user execution
- Health checks configured for all services
- Volume permissions correctly set
- Graceful shutdown handling

### TO-3: CI/CD Pipeline Implementation

**Objective**: Automate testing and code quality checks (CI only, no deployment automation).

**Success Criteria**:
- Automated test execution on pull requests
- Linting (flake8, black, mypy) integrated
- Test coverage reporting
- Docker image build validation
- CI runs in under 5 minutes

### TO-4: Logging and Observability

**Objective**: Improve system observability for debugging and monitoring.

**Success Criteria**:
- Structured JSON logging implemented
- Request/response logging with correlation IDs
- Error tracking with stack traces
- Performance metrics logged (response times)
- Log aggregation compatible (ELK, CloudWatch, etc.)

### TO-5: Frontend Integration Readiness

**Objective**: Prepare backend for Angular frontend integration.

**Success Criteria**:
- CORS properly configured
- API versioning strategy defined
- Consistent response formats
- Error handling suitable for UI display
- API documentation accessible to frontend team

### TO-6: Cloud Deployment Preparation

**Objective**: Ensure system is ready for cloud deployment without vendor lock-in.

**Success Criteria**:
- Docker images compatible with major cloud providers
- Environment-based configuration
- Secrets management strategy defined
- Database backup/restore procedures documented
- Scaling strategy documented

---

## 6. Constraints

### C-1: Technology Constraints

**C-1.1**: The system MUST continue using FastAPI, DuckDB, and Docker (no stack replacement).

**C-1.2**: The system MUST remain compatible with Python 3.12.

**C-1.3**: All dependencies MUST use prebuilt wheels (no source compilation required).

### C-2: Data Constraints

**C-2.1**: The database schema MUST NOT be modified (existing schema is source of truth).

**C-2.2**: Existing SQL queries MUST NOT be changed unless fixing bugs.

**C-2.3**: Column names and data types MUST match the current schema.sql.

### C-3: Operational Constraints

**C-3.1**: The system MUST support Windows development environments.

**C-3.2**: The ELT pipeline MUST remain a standalone script executable outside Docker.

**C-3.3**: The API MUST be backward compatible with any existing consumers.

### C-4: Resource Constraints

**C-4.1**: Docker images SHOULD be under 500MB compressed.

**C-4.2**: The API SHOULD use less than 512MB RAM per worker.

**C-4.3**: The pipeline SHOULD complete within 10 minutes for typical datasets.

---

## 7. Assumptions

**A-1**: PocketBase will remain available as a data source, but the system can operate without it.

**A-2**: The Spotify dataset schema will remain stable (no new columns added frequently).

**A-3**: The system will initially serve a single-tenant use case (no multi-tenancy required).

**A-4**: Frontend will be developed separately and consume the API via HTTP.

**A-5**: Cloud deployment will use managed container services (not bare VMs).

**A-6**: CI/CD will run on GitHub Actions or similar cloud-based CI platform.

---

## 8. Dependencies

**D-1**: PocketBase service (optional, for data ingestion)

**D-2**: Docker runtime (for containerized deployment)

**D-3**: Python 3.12 runtime (for local development)

**D-4**: CI/CD platform (GitHub Actions, GitLab CI, or similar)

**D-5**: Cloud provider (AWS, GCP, Azure, or similar) for production deployment

**D-6**: Frontend development team (for Angular integration)

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **ELT** | Extract, Load, Transform - data pipeline pattern |
| **DuckDB** | Embedded analytical database optimized for OLAP queries |
| **PocketBase** | Open-source backend with file storage and authentication |
| **FastAPI** | Modern Python web framework for building APIs |
| **Dimensional Model** | Data warehouse design with facts and dimensions |
| **Parquet** | Columnar storage format for analytical data |
| **CORS** | Cross-Origin Resource Sharing - browser security mechanism |
| **OpenAPI** | API specification standard (formerly Swagger) |
| **Uvicorn** | ASGI web server for Python |
| **Multi-stage Build** | Docker technique to minimize image size |

---

## 10. Acceptance Criteria

### AC-1: Backend Professionalization

- [ ] All existing endpoints remain functional
- [ ] OpenAPI documentation is complete with examples
- [ ] Error responses follow consistent format
- [ ] CORS is configurable via environment variables

### AC-2: Docker Stability

- [ ] `docker compose up` successfully starts all services
- [ ] Health checks pass for API and PocketBase
- [ ] Volumes persist data across restarts
- [ ] Non-root user execution verified

### AC-3: Testing

- [ ] Critical API endpoints have automated tests
- [ ] Pipeline has tests for data normalization
- [ ] Tests pass with `pytest` command
- [ ] Coverage report is generated

### AC-4: CI/CD

- [ ] CI pipeline runs tests on pull requests
- [ ] Linting checks pass (flake8, black, mypy)
- [ ] Docker image builds successfully
- [ ] CI completes in under 5 minutes

### AC-5: Observability

- [ ] Structured JSON logging implemented
- [ ] Request/response logging includes correlation IDs
- [ ] Error logs include stack traces
- [ ] Performance metrics are logged

### AC-6: Frontend Readiness

- [ ] CORS allows frontend origin
- [ ] API documentation is accessible
- [ ] Response formats are consistent
- [ ] Error messages are user-friendly

### AC-7: Cloud Readiness

- [ ] Docker images are cloud-agnostic
- [ ] Environment-based configuration works
- [ ] Secrets management strategy documented
- [ ] Scaling strategy documented

---

## 11. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| API Response Time (p95) | < 500ms | Application logs |
| Pipeline Execution Time | < 5 minutes | Pipeline logs |
| Test Coverage | > 70% | Coverage report |
| CI Pipeline Duration | < 5 minutes | CI platform metrics |
| Docker Image Size | < 500MB | Docker inspect |
| API Uptime | > 99% | Health check monitoring |
| Documentation Completeness | 100% endpoints | Manual review |

---

## 12. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| DuckDB version incompatibility | High | Low | Pin DuckDB version, test upgrades in staging |
| PocketBase API changes | Medium | Medium | Maintain Parquet fallback, version PocketBase |
| Docker volume permission issues | Medium | Low | Document volume setup, use named volumes |
| CI/CD platform limitations | Low | Low | Choose platform with Docker support |
| Frontend CORS issues | Medium | Medium | Test CORS early, document configuration |
| Cloud provider lock-in | High | Low | Use cloud-agnostic Docker approach |

---

## 13. Future Enhancements (Out of Scope)

- Authentication and authorization (JWT, OAuth)
- Rate limiting and API quotas
- Caching layer (Redis)
- Real-time data updates (WebSockets)
- Advanced analytics (ML models)
- Multi-tenancy support
- GraphQL API alternative
- Automated deployment (CD)
- Blue-green deployment strategy
- Database replication and sharding

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-16  
**Status**: Draft
