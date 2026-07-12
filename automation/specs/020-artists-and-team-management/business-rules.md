# Business Rules — Spec 020

1. **Organization scoping.** Every read/write is scoped by
   `X-Organization-Id`; an artist profile belonging to org A is invisible
   and unmutable from org B's context (`NotFoundError` on cross-org access,
   verified in `test_artists_security_m5.py`).
2. **Duplicate prevention.** `CreateArtistProfile` normalizes
   `display_name` (NFKD-strip accents, lowercase, collapse whitespace) and
   rejects a second artist with the same `normalized_name` within the same
   organization (`DuplicateArtistError`). The same normalized name IS
   allowed across different organizations.
3. **Status lifecycle.** `draft → active ⇄ inactive → archived` only.
   `archived` is terminal. Any other transition raises
   `InvalidTransitionError`. Every transition appends a row to
   `app_artist_status_history` (`from_status`, `to_status`, `reason`,
   `actor_user_id`, `at`) and an audit-log entry.
4. **Warehouse link is optional and one-directional.** `LinkWarehouseArtist`
   requires the target `dim_artista.id_artista` to exist
   (`WarehouseArtistNotFoundError` otherwise) but never writes to
   `dim_artista`. Unlinking is not exposed (no destructive change to the
   optional pointer once verified valid — accepted debt if unlink is later
   needed).
5. **Manager assignment.** `AssignManager` allows only one **active**
   assignment per `(artist_id, user_id)` pair; re-assigning the same user
   while active raises `ConflictError`. Ending an assignment
   (`end_assignment`) sets `status='ended'` + `ended_at`; a new assignment
   can then be created for the same user.
6. **Team membership.** `AddTeamMember` / `RemoveTeamMember` follow the same
   active/removed pattern as assignments, independent of manager
   assignments (a user can be both a manager and a team member with a
   different `team_role`).
7. **External identifiers are upserts.** `SetExternalIdentifier` updates the
   existing `(artist_id, system_code)` row's `external_value` if present,
   otherwise inserts a new row — never creates duplicates.
8. **Transfer is audited-only.** `TransferArtistOrganization` moves
   `organization_id` on the profile and ends the old primary
   `app_artist_organization` link while creating a new primary link for the
   target organization; it does not validate target-organization
   membership (explicitly out of scope) and always writes a full
   before/after audit entry.
9. **No destructive DuckDB changes.** No `DROP`, `TRUNCATE`, or destructive
   `ALTER` against any pre-existing table. All schema additions are
   idempotent `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`.
10. **Audit on every mutation.** All use cases that change state call the
    shared `_audit()` helper (mirroring billing's pattern), writing to
    `app_audit_log` via `AuditRepository`.
