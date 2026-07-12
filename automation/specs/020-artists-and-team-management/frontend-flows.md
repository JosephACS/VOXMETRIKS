# Frontend Flows — Spec 020

Package: `apps/frontend/src/app/packages/artists/`. Routes mounted under
`/artist-profiles` (not `/artists` — see plan.md decision #3).

## Pages
1. **`artist-profiles-list.page.ts`** (`/artist-profiles`)
   - Status filter (draft/active/inactive/archived/all)
   - Create-artist form (display name, optional legal name)
   - Table with name, status badge, warehouse-link indicator badge, link to detail
2. **`artist-profile-detail.page.ts`** (`/artist-profiles/:id`)
   - Profile card (status, legal name, normalized name, warehouse link indicator)
   - Lifecycle actions: Activate / Deactivate / Archive (conditionally shown
     based on current status)
   - Warehouse-link form (`LinkWarehouseArtist`)
   - Transfer-organization form (`TransferArtistOrganization`)
   - Organization links list
   - Links to Team and History sub-pages
3. **`artist-profile-team.page.ts`** (`/artist-profiles/:id/team`)
   - Manager assignments: assign form + list with "End" action
   - Team members: add form + list with "Remove" action
4. **`artist-profile-history.page.ts`** (`/artist-profiles/:id/history`)
   - Read-only status-history table (from/to/reason/actor/at)

## Service
`services/artists-api.service.ts` (`ArtistsApiService`) wraps all 17
backend endpoints, using `environment.apiUrl` and an `X-Organization-Id`
header built from the active organization (via
`OrganizationContextService.activeOrganization()`).

## Navigation & i18n
- New nav section `nav.section.artistProfiles` ("Artists & Team" / "Artistas
  y Equipo") added to `dashboard-layout.component.ts`, linking to
  `/artist-profiles`.
- i18n keys added to `core/i18n/locales/en.ts` and `es.ts`:
  `nav.section.artistProfiles`, `nav.artistProfiles.list`.
- Deliberately reuses **new** keys distinct from the pre-existing
  `nav.artists` (streaming/catalog artists) to avoid key collisions.

## Testing
`services/artists-l4.spec.ts` — `HttpTestingController`-based unit spec
covering list/create/get/activate/link-warehouse/transfer/history/
assignManager/addTeamMember/setExternalIdentifier (10 tests, all passing).
Uses `TestBed.resetTestingModule()` per the project convention.

Playwright E2E for these pages is **NOT_VERIFIED** (accepted debt).
