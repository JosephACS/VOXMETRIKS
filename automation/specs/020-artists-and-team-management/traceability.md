# Traceability — Spec 020

| Requirement | Implementation | Test |
|---|---|---|
| `app_artist_profile` table + lifecycle | `infrastructure/schema.py::_create_artist_profile` | `test_artists_schema_m1.py` |
| `app_artist_organization` | `_create_artist_organization` | `test_artists_schema_m1.py` |
| `app_artist_assignment` | `_create_artist_assignment` | `test_artists_schema_m1.py` |
| `app_artist_team_member` | `_create_artist_team_member` | `test_artists_schema_m1.py` |
| `app_artist_external_identifier` | `_create_artist_external_identifier` | `test_artists_schema_m1.py` |
| `app_artist_status_history` | `_create_artist_status_history` | `test_artists_schema_m1.py` |
| CreateArtistProfile (+ dedupe) | `ArtistProfileUseCases.create` | `test_artists_use_cases_m2.py::test_create_artist_profile*` |
| ActivateArtist/DeactivateArtist/ArchiveArtist | `ArtistProfileUseCases.activate/deactivate/archive` | `test_artists_use_cases_m2.py::test_status_transitions*` |
| LinkOrganization | `ArtistOrganizationUseCases.link` | `test_artists_use_cases_m2.py::test_link_organization*` |
| AssignManager / end | `ArtistAssignmentUseCases.assign_manager/end_assignment` | `test_artists_use_cases_m2.py::test_assign_manager*` |
| AddTeamMember / RemoveTeamMember | `ArtistTeamUseCases.add_member/remove_member` | `test_artists_use_cases_m2.py::test_*team_member*` |
| SetExternalIdentifier | `ArtistExternalIdentifierUseCases.set_identifier` | `test_artists_use_cases_m2.py::test_set_external_identifier*` |
| LinkWarehouseArtist | `ArtistProfileUseCases.link_warehouse_artist` | `test_artists_use_cases_m2.py::test_link_warehouse_artist` |
| TransferArtistOrganization | `ArtistProfileUseCases.transfer_organization` | `test_artists_use_cases_m2.py::test_transfer_artist_organization` |
| ListArtists / GetArtist / GetHistory | `ArtistProfileUseCases.list/get`, `ArtistHistoryUseCases.get_history` | `test_artists_use_cases_m2.py` |
| REST API (17 endpoints) | `presentation/router.py` | `test_artists_api_m3.py` |
| `artist.*` permissions + role matrix | `organizations/infrastructure/catalogs.py` | `test_organizations_schema_i1.py`, `test_artists_schema_m1.py` (permission-seeded tests) |
| Cross-org isolation | `_get_or_raise_for_org` in `use_cases.py` | `test_artists_security_m5.py::test_cross_tenant_*` |
| Audit entries | `_audit()` in `use_cases.py` | `test_artists_security_m5.py::test_audit_entry_*` |
| `dim_artista` non-mutation | read-only `_assert_warehouse_artist_exists` | `test_artists_schema_m1.py`, `test_artists_security_m5.py` |
| Frontend list/detail/team/history pages | `apps/frontend/src/app/packages/artists/pages/*` | `services/artists-l4.spec.ts` (API layer); pages manually reviewed |
| Frontend nav + i18n | `dashboard-layout.component.ts`, `core/i18n/locales/{en,es}.ts` | manual review |
