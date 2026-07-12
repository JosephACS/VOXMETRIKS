# Test Strategy — Spec 020

Mirrors the L1–L5 (here M1–M5) layering used by billing/CRM/subscriptions.

| Level | File | Focus | Count |
|---|---|---|---|
| M1 | `tests/test_artists_schema_m1.py` | Table existence, idempotent `ensure_artist_tables`, CHECK constraints, permission seeding, `dim_artista` untouched | 21 |
| M2 | `tests/test_artists_use_cases_m2.py` | All 13 use cases incl. duplicates, transitions, cross-org isolation, assignment/team lifecycle, external-identifier upsert, warehouse link, transfer | 25 |
| M3 | `tests/test_artists_api_m3.py` | Full HTTP surface via `TestClient`, incl. missing `X-Organization-Id` header | 14 |
| M5 | `tests/test_artists_security_m5.py` | Cross-tenant isolation, audit entries, `dim_artista` non-mutation, viewer permission denial | 10 |
| FE | `services/artists-l4.spec.ts` | `ArtistsApiService` HTTP contract smoke tests | 10 |

**Total backend: 70 tests, all passing.**
**Total frontend (artists-specific): 10 tests, all passing.**
**Full backend suite (517+ tests across all packages): all passing** —
no regressions introduced in billing/CRM/subscriptions/organizations/etc.

## Run commands
```bash
cd apps/backend
python -m pytest tests/test_artists_*.py -q     # 70 passed
python -m pytest -q                              # full suite, all passed

cd apps/frontend
npx ng test --no-watch --no-progress --include=**/artists-l4.spec.ts   # 10 passed
npx ng build --configuration development                                # compiles clean
```

## Coverage notes
- Org isolation verified at both use-case level (`NotFoundError` on
  cross-org `get`/mutate) and API level (403/404).
- Duplicate prevention verified for artist name (per org), external
  identifier (per artist+system, via upsert-not-duplicate), and manager
  assignment (per artist+user while active).
- Status transitions verified for all valid edges and at least one invalid
  edge (`InvalidTransitionError`).
- Audit entries verified present after create/transition/transfer.
- Warehouse link verified to require an existing `dim_artista` row and to
  never mutate `dim_artista`.
- Permission denial verified for `viewer` role attempting create/assign.

## Known gap
Playwright browser E2E was **not** run for this spec (NOT_VERIFIED) — the
backend + API + security + FE-unit layers give strong confidence, but no
live-browser click-through was captured. See `evidence/accepted-debt.md`.
