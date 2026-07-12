# Plan — Spec 021 Catalog Rights and Contracts

## Architecture
Package-by-domain, mirroring `apps/backend/app/packages/artists/` and `billing/`:

```
apps/backend/app/packages/catalog_rights/
  domain/        entities.py, errors.py
  application/   use_cases.py
  infrastructure/ schema.py (ensure_catalog_rights_tables)
  presentation/  schemas.py, dependencies.py, error_mapping.py, router.py

apps/frontend/src/app/packages/catalog-rights/
  models/catalog-rights.models.ts
  services/catalog-rights-api.service.ts (+ catalog-rights-l4.spec.ts)
  pages/  catalog-assets-list, catalog-asset-detail (coverage),
          catalog-releases-list, rights-contracts-list,
          rights-contract-detail (approvals), rights-contract-history,
          rights-conflicts-list
  catalog-rights.routes.ts
```

## Milestones
- **M0** — Docs scaffold + evidence/m0-setup.md
- **N1** — Schema (11 tables, idempotent `ensure_catalog_rights_tables`)
- **N2** — Use cases (16 operations, sweep-line overlap detection)
- **N3** — Presentation + API wiring under `/api/v1/catalog-rights`
- **N4** — Permissions in `organizations/infrastructure/catalogs.py`
- **N5** — Backend tests (schema/use-cases/API/security)
- **N6** — Frontend package (models, service, pages, routes, nav, i18n) + FE unit spec
- **Closure** — evidence/spec-closure.md + accepted-debt.md

## Key decisions
1. **`app_rights_contract` ≠ `app_commercial_contract`** — CRM sales contracts (Spec 017) and legal-rights contracts (this spec) are separate tables, domains, and APIs; never joined.
2. **Percentage validation is scoped** — never a naive global sum per asset; sweep-line algorithm per `(asset_id, rights_type, territory_code)` across overlapping `[valid_from, valid_to]` periods.
3. **WORLD territory scope** — contracts with no explicit `app_rights_territory` rows are treated as `WORLD` and overlap every explicit territory for the same asset/rights_type.
4. **Warehouse link optional** — `warehouse_track_id` validated against `dim_track.id_track` (read-only); `warehouse_album_id` stored without existence check (no `dim_album` table).
5. **No SQL compound UNIQUE constraints** — natural-key uniqueness enforced in use cases (consistent with artists/billing DuckDB posture).
6. **UI copy** — "recorded"/"tracked" only; never "certified" or "legally valid".

## Wiring
- `main.py`: `ensure_catalog_rights_tables` in startup; `catalog_rights_router` at `/api/v1`
- `conftest.py`: schema bootstrap includes catalog_rights tables + minimal `dim_track`

## Preceding spec
020 Artists and Team Management (`app_artist_profile` linkage for assets/parties).
