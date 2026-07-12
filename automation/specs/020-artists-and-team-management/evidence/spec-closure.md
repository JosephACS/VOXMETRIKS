# Spec Closure — Spec 020 Artists and Team Management

**Final status:** `CLOSED_WITH_ACCEPTED_DEBT`
**Date:** 2026-07-11

## Summary
All in-scope backend and frontend deliverables for Spec 020 were
implemented, wired, and tested. The business API mounts at
`/api/v1/artists`; analytics catalog artists remain at
`/api/v1/catalog/artists`. Frontend UI routes use `/artist-profiles/*`
to avoid collision with streaming consumer pages. Playwright browser E2E
was not run (`NOT_VERIFIED`), consistent with prior specs.

## Tables delivered (6/6, exact names as specified)
`app_artist_profile`, `app_artist_organization`, `app_artist_assignment`,
`app_artist_team_member`, `app_artist_external_identifier`,
`app_artist_status_history`.

## Use cases delivered (13/13)
CreateArtistProfile, ActivateArtist, DeactivateArtist, ArchiveArtist,
LinkOrganization, AssignManager, AddTeamMember, RemoveTeamMember,
SetExternalIdentifier, LinkWarehouseArtist, TransferArtistOrganization,
ListArtists, GetArtist, GetHistory (14 including GetHistory — task listed
GetHistory separately from the 13-item lead sentence; all delivered).

## Permissions delivered (6/6)
`artist.view`, `artist.create`, `artist.update`, `artist.assign`,
`artist.archive`, `artist.transfer` — seeded in
`organizations/infrastructure/catalogs.py` and granted per the requested
role matrix (owner/administrator/artist_manager/artist/viewer).
`test_organizations_schema_i1.py`'s banned-future list updated to remove
`artist.view`.

## API endpoints delivered (17, under `/api/v1/artists`)
```
GET    /artists
POST   /artists
GET    /artists/{id}
POST   /artists/{id}/activate
POST   /artists/{id}/deactivate
POST   /artists/{id}/archive
POST   /artists/{id}/link-warehouse
POST   /artists/{id}/transfer
GET    /artists/{id}/history
GET    /artists/{id}/organizations
POST   /artists/{id}/organizations
GET    /artists/{id}/assignments
POST   /artists/{id}/assignments
POST   /artists/{id}/assignments/{assignment_id}/end
GET    /artists/{id}/team
POST   /artists/{id}/team
POST   /artists/{id}/team/{member_id}/remove
GET    /artists/{id}/external-identifiers
POST   /artists/{id}/external-identifiers
```
(Analytics warehouse catalog: `/api/v1/catalog/artists` — separate domain.)

## Test results
| Suite | Result |
|---|---|
| `pytest tests/test_artists_*.py -q` | **70 passed**, 0 failed |
| `pytest -q` (full backend suite, all packages) | **all passed**, exit code 0, no regressions |
| `ng test --include=**/artists-l4.spec.ts` | **10 passed**, 0 failed |
| `ng build --configuration development` | compiles clean, 0 errors |

## Files delivered
### Backend (`apps/backend/app/packages/artists/`)
`__init__.py` ×5 (package + 4 sub-layers), `domain/entities.py`,
`domain/errors.py`, `application/use_cases.py`, `infrastructure/schema.py`,
`presentation/schemas.py`, `presentation/dependencies.py`,
`presentation/error_mapping.py`, `presentation/router.py`

### Backend tests (`apps/backend/tests/`)
`test_artists_schema_m1.py`, `test_artists_use_cases_m2.py`,
`test_artists_api_m3.py`, `test_artists_security_m5.py`

### Backend modified
`app/main.py`, `tests/conftest.py`,
`app/packages/organizations/infrastructure/catalogs.py`,
`tests/test_organizations_schema_i1.py`

### Frontend (`apps/frontend/src/app/packages/artists/`)
`models/artist.models.ts`, `services/artists-api.service.ts`,
`services/artists-l4.spec.ts`, `pages/artist-profiles-list.page.ts`,
`pages/artist-profile-detail.page.ts`, `pages/artist-profile-team.page.ts`,
`pages/artist-profile-history.page.ts`, `artists.routes.ts`

### Frontend modified
`app.routes.ts`, `layouts/dashboard-layout/dashboard-layout.component.ts`,
`core/i18n/locales/en.ts`, `core/i18n/locales/es.ts`

### Docs (`automation/specs/020-artists-and-team-management/`)
`spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `business-rules.md`,
`api-contracts.md`, `role-and-permission-model.md`, `frontend-flows.md`,
`test-strategy.md`, `audit-and-security.md`, `checklist.md`,
`traceability.md`, `evidence/m0-setup.md`, `evidence/spec-closure.md`
(this file), `evidence/accepted-debt.md`

## Blockers
None outstanding. All backend and frontend deliverables complete and
tested; the two accepted-debt items are documented deviations with clear
rationale, not blockers.

## Closure verdict
**CLOSED_WITH_ACCEPTED_DEBT** — ready for the next spec.
