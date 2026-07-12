# Plan — Spec 020 Artists and Team Management

## Architecture
Package-by-domain, mirroring `apps/backend/app/packages/billing/`:

```
apps/backend/app/packages/artists/
  domain/        entities.py, errors.py
  application/    use_cases.py
  infrastructure/ schema.py
  presentation/   schemas.py, dependencies.py, error_mapping.py, router.py

apps/frontend/src/app/packages/artists/
  models/artist.models.ts
  services/artists-api.service.ts (+ artists-l4.spec.ts)
  pages/  artist-profiles-list.page.ts, artist-profile-detail.page.ts,
          artist-profile-team.page.ts, artist-profile-history.page.ts
  artists.routes.ts
```

## Milestones
- **M0** — Docs scaffold (this folder) + evidence/m0-setup.md
- **M1** — Schema (6 tables, idempotent `ensure_artist_tables`)
- **M2** — Use cases (all 13 operations + helpers)
- **M3** — Presentation (schemas, dependencies, error mapping, router) + API wiring
- **M4** — Permissions in `organizations/infrastructure/catalogs.py` + role matrix
- **M5** — Backend tests (schema/use-cases/API/security) + security hardening
- **M6** — Frontend package (models, service, pages, routes, nav, i18n) + FE spec
- **Closure** — evidence/spec-closure.md + accepted-debt.md, spec.md status update

## Key decisions
1. **API prefix `/api/v1/artists` (business) vs `/api/v1/catalog/artists`
   (analytics)** — business artist profiles mount at `/api/v1/artists`;
   the warehouse catalog router uses `/api/v1/catalog/artists`
   (`dim_artista`-backed). Frontend UI routes remain `/artist-profiles/*`
   to distinguish from streaming consumer pages at `/artists/*`.
2. **No SQL `UNIQUE` compound indexes on mutated columns** — DuckDB has a
   known limitation (see `data-model.md`) where a secondary index on a
   column later touched by `UPDATE` can raise a spurious `PRIMARY KEY`
   `ConstraintException`. Natural-key uniqueness is enforced in
   `use_cases.py` instead; profile field mutations use an atomic
   `DELETE + re-INSERT` of the same row rather than `UPDATE`.
3. **Frontend route `/artist-profiles`** mirrors the backend prefix and
   avoids colliding with the existing `/artists` and `/artists/:id` routes
   used by the streaming/catalog artists feature.
4. Reuse `AuditRepository`, `X-Organization-Id` header pattern, and
   `app_role_permission` join exactly as billing does — no new RBAC
   primitives introduced.

## Shell commands used
```
python -m pytest tests/test_artists_*.py -q
python -m pytest -q                     # full backend suite
npx ng build --configuration development
npx ng test --no-watch --no-progress --include=**/artists-l4.spec.ts
```
