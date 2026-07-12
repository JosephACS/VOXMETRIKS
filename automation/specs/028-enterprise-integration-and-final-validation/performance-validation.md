# Performance Validation — Spec 028

**Context:** Academic/demo deployment on DuckDB — no SLA claims.

## Measured gates (documented)

| Gate | Result | Notes |
|------|--------|-------|
| Backend pytest full suite | **~737 tests** (revalidating) | CI: `python -m pytest -q` |
| Golden path smoke | **10 tests** | Sub-second in isolation DB |
| FE unit tests | **179 PASS** | `npm test` |
| FE lint | **0 errors / 15 warnings** | `npm run lint` |
| FE build | **PASS** | `npm run build` |

## Not verified

| Item | Status |
|------|--------|
| Load test (k6/locust) | **NOT_VERIFIED** |
| Playwright E2E timing | **NOT_VERIFIED** |
| Docker compose cold start | **NOT_VERIFIED** |
| Warehouse at production scale (>10GB) | **NOT_VERIFIED** |

## Architectural performance notes

- Shared read-only DuckDB connection for API reads (`open_read_pool`)
- Write serialization via global lock — safe, not high-throughput
- Pagination on list endpoints (`page`, `page_size`)
- Secondary indexes on hot columns where DuckDB ART allows
- Background jobs optional (`JOBS_ENABLED=false` in CI)

## Acceptable academic thresholds

- API p95 < 2s on dev laptop for list endpoints with <10k rows: **assumed OK**, not benchmarked
- ELT full pipeline: runtime depends on Parquet size; not a 028 gate

## Recommendations for production (deferred)

- Migrate app tables to PostgreSQL for concurrency
- Add Redis cache for dashboard aggregates
- Separate read replicas for analytics
