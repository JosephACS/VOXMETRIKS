# Accepted Debt — Spec 020

Status at closure: **CLOSED_WITH_ACCEPTED_DEBT**

## 1. API vs UI route prefix (resolved at backend, UI debt remains)
The original closure mounted business artist profiles at
`/api/v1/artist-profiles` to avoid colliding with the analytics catalog
router. **Subsequently resolved:** the business router now mounts at
**`/api/v1/artists`** (see `artists/presentation/router.py` module
docstring). Analytics warehouse catalog artists remain at
**`/api/v1/catalog/artists`** (`dim_artista`-backed streaming domain).

The **frontend UI** still uses `/artist-profiles/*` routes to avoid
confusion with the streaming consumer pages at `/artists/*`. The API
service (`artists-api.service.ts`) calls `/api/v1/artists`.

**Risk:** low — backend API matches the requested `/artists` prefix;
integrators use `/api/v1/artists`. UI path divergence is cosmetic only.

## 2. No SQL `UNIQUE` compound constraints on mutated columns
DuckDB has a known limitation (https://duckdb.org/docs/sql/indexes) where a
secondary index on a column that is later the target of an `UPDATE` can, in
combination with certain connection open/close/reopen sequences against a
persisted (file-backed) database, raise a spurious `PRIMARY KEY`
`ConstraintException` even when no duplicate primary key exists. This was
reproduced concretely on `app_artist_profile` during `LinkWarehouseArtist`
and `TransferArtistOrganization` under the API/TestClient (real
connection-pool-like usage), not just in isolated unit tests.

**Decision:**
1. Removed all compound `UNIQUE` constraints from artists tables; natural-
   key uniqueness ((org, normalized_name), (artist, system_code),
   (artist, org)) is enforced in `use_cases.py` before insert.
2. All `app_artist_profile` field mutations go through `_update_profile_row()`,
   which performs an atomic `DELETE` + re-`INSERT` of the same row (same
   `id`) instead of `UPDATE`, fully avoiding the DuckDB `UPDATE` code path
   implicated in the bug.

**Risk:** low-medium — enforced only in the application layer, so a direct
SQL client bypassing `use_cases.py` could theoretically insert a duplicate.
Acceptable because all production access goes through the use-case layer
(same posture already accepted for other packages, e.g. billing/CRM
duplicate email checks). Regression-tested by
`test_artists_use_cases_m2.py::test_create_artist_profile_duplicate_rejected`
and equivalents for external identifiers and assignments.

## 3. Playwright E2E browser verification — NOT_VERIFIED
No live-browser Playwright run was performed against the new frontend
pages (`artist-profiles-list`, `artist-profile-detail`,
`artist-profile-team`, `artist-profile-history`). Confidence instead comes
from:
- Backend API test suite (`test_artists_api_m3.py`, 14 tests) exercising
  every endpoint the frontend calls.
- Frontend service-layer unit tests (`artists-l4.spec.ts`, 10 tests)
  verifying every HTTP contract (`method`, `URL`, headers, body shape).
- `ng build --configuration development` compiling without errors,
  confirming type-correctness of all new components/templates/routes.

**Risk:** low-medium — visual/interaction regressions (e.g. a broken
`@if`/`@for` binding, a missing import) would not be caught until manual
or E2E testing. Recommended follow-up: add a Playwright spec for the
artist-profiles create → activate → assign-manager → archive flow in a
future spec/iteration.

## 4. Unlink warehouse artist not exposed
`LinkWarehouseArtist` can set the pointer but there is no `UnlinkWarehouseArtist`
use case/endpoint. Not required by the task description; can be added
later if a correction workflow is needed. Low risk — the link is
non-destructive metadata only.

## 5. `TransferArtistOrganization` does not validate target org existence beyond FK-less reference
The use case moves `organization_id` without checking that the target
organization has any relationship to the actor's permissions (i.e., an
`artist.transfer` holder in org A can transfer an artist to any
`organization_id` integer, including a non-existent one). This matches the
"audited only" instruction in the task (no extra validation requested) and
is fully audited via `app_artist_status_history`-adjacent audit log entries
and the `app_artist_organization` primary-link swap. Low risk given
`artist.transfer` is an owner-only permission by default.
