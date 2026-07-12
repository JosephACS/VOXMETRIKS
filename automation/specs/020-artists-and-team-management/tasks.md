# Tasks — Spec 020

- [x] T1 — Docs scaffold (`automation/specs/020-artists-and-team-management/`)
- [x] T2 — Domain layer: `entities.py`, `errors.py`
- [x] T3 — Infrastructure: `schema.py` (6 tables, idempotent)
- [x] T4 — Application: `use_cases.py` (13 use cases + helpers)
- [x] T5 — Presentation: `schemas.py`, `dependencies.py`, `error_mapping.py`, `router.py`
- [x] T6 — Permissions: `organizations/infrastructure/catalogs.py`
  (`PERMISSIONS` + `ROLE_PERMISSION_MATRIX`)
- [x] T7 — Update `test_organizations_schema_i1.py` banned-permissions list
- [x] T8 — Wire `main.py` (`ensure_artist_tables` + `include_router`) and
  `tests/conftest.py` (`ensure_artist_tables`)
- [x] T9 — Backend tests: M1 (schema), M2 (use cases), M3 (API), M5 (security)
- [x] T10 — Root-cause + fix DuckDB `ConstraintException` on `UPDATE`
  (see `data-model.md` / `accepted-debt.md`)
- [x] T11 — Fix module-scoped `schema_bootstrap._schema_ready` fixture leak
  in M1/M2/M5 test fixtures (restore immediately after `ensure_*` calls,
  not at teardown)
- [x] T12 — Frontend: models, `ArtistsApiService`, 4 pages, `artists.routes.ts`
- [x] T13 — Wire frontend: `app.routes.ts`, dashboard nav, i18n (en/es)
- [x] T14 — Frontend unit spec `artists-l4.spec.ts`
- [x] T15 — Full backend suite re-run (regression check)
- [x] T16 — Frontend build + targeted test run (regression check)
- [x] T17 — `evidence/spec-closure.md` + `evidence/accepted-debt.md`
- [x] T18 — Update `spec.md` status to `CLOSED_WITH_ACCEPTED_DEBT`
