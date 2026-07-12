# Checklist — Spec 020

- [x] Docs scaffold created (`spec.md`, `plan.md`, `tasks.md`, `data-model.md`,
  `business-rules.md`, `api-contracts.md`, `role-and-permission-model.md`,
  `frontend-flows.md`, `test-strategy.md`, `audit-and-security.md`,
  `checklist.md`, `traceability.md`, `evidence/`)
- [x] 6 tables created exactly as specified (`app_artist_profile`,
  `app_artist_organization`, `app_artist_assignment`,
  `app_artist_team_member`, `app_artist_external_identifier`,
  `app_artist_status_history`)
- [x] 13 use cases implemented (Create/Activate/Deactivate/Archive/
  LinkOrganization/AssignManager/AddTeamMember/RemoveTeamMember/
  SetExternalIdentifier/LinkWarehouseArtist/TransferArtistOrganization/
  ListArtists/GetArtist/GetHistory)
- [x] 6 permissions added + role matrix updated (owner/administrator/
  artist_manager/artist/viewer)
- [x] `test_organizations_schema_i1.py` banned-list updated (removed
  `artist.view`)
- [x] API router wired into `main.py` (`ensure_artist_tables` +
  `include_router`) and `tests/conftest.py`
- [x] Frontend package created (models, service, 4 pages, routes)
- [x] Frontend wired into `app.routes.ts`, dashboard nav, i18n (en/es)
- [x] Backend tests: schema (M1), use-cases (M2), API (M3), security (M5) —
  70/70 passing
- [x] Frontend unit spec for `ArtistsApiService` — 10/10 passing
- [x] Full backend suite re-run after changes — all passing, no regressions
- [x] Frontend build (`ng build`) — compiles clean
- [x] `evidence/spec-closure.md` + `evidence/accepted-debt.md` written
- [x] `spec.md` status updated to `CLOSED_WITH_ACCEPTED_DEBT`
- [ ] Playwright E2E browser verification — NOT_VERIFIED (accepted debt)
