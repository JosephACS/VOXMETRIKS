# Spec 020 — Artists and Team Management

**Feature:** Artists and Team Management
**Status:** CLOSED_WITH_ACCEPTED_DEBT
**Version:** 1.0.0
**Date:** 2026-07-11
**Preceding spec:** 019 Billing, Payments and Reconciliation (CLOSED_WITH_ACCEPTED_DEBT)

---

## 1. Purpose

Deliver organization-scoped **business** artist-profile and team-management
capabilities for Voxmetriks, distinct from the analytics warehouse artist
dimension:

- Business artist profiles (`app_artist_profile`) with a lifecycle
  (draft → active ⇄ inactive → archived)
- Organization ↔ artist linkage, including primary-ownership transfer
- Manager assignment and general team membership per artist
- External identifiers (e.g. Spotify/Apple artist IDs) per artist
- Append-only status-change history for audit
- Optional, non-destructive link to the analytics warehouse artist
  (`dim_artista`) for reporting continuity — never the reverse

---

## 2. Scope

### In scope
- `app_artist_profile` — organization-scoped business artist record
- `app_artist_organization` — artist↔organization relationship (primary/secondary/licensed/partner)
- `app_artist_assignment` — manager assignment (user_id, role, active/ended)
- `app_artist_team_member` — general team membership (user_id, team_role, active/removed)
- `app_artist_external_identifier` — per-system external id (e.g. spotify, apple_music)
- `app_artist_status_history` — append-only status-transition trail
- Use cases: CreateArtistProfile, ActivateArtist, DeactivateArtist, ArchiveArtist,
  LinkOrganization, AssignManager, AddTeamMember, RemoveTeamMember,
  SetExternalIdentifier, LinkWarehouseArtist, TransferArtistOrganization,
  ListArtists, GetArtist, GetHistory
- Permissions: `artist.view`, `artist.create`, `artist.update`, `artist.assign`,
  `artist.archive`, `artist.transfer`
- REST API under `/api/v1/artist-profiles` (see accepted-debt.md for the
  prefix decision)
- Frontend package `apps/frontend/src/app/packages/artists/`

### Out of scope
- Any mutation of `dim_artista` or the ELT/streaming/music-catalog domain
  (read-only existence lookups only, for `LinkWarehouseArtist`)
- Royalty/financial splits between team members (future spec)
- Contract-level artist terms (already covered by `contracts` package;
  no duplication here)
- Playwright E2E browser verification (NOT_VERIFIED; see accepted-debt.md)

---

## 3. Business rules summary
See `business-rules.md` for the full set. Key rules:

1. `app_artist_profile` is organization-scoped; duplicate `display_name`
   (case/accent/whitespace-insensitive) within the same organization is
   rejected (`DuplicateArtistError`).
2. Status transitions are restricted to a fixed state machine
   (see `data-model.md`); invalid transitions raise `InvalidTransitionError`.
3. `warehouse_artist_id` is optional and, when set, must reference an
   existing `dim_artista.id_artista` row — but the reverse link is never
   written and `dim_artista` is never mutated.
4. `TransferArtistOrganization` is an audited-only move of the artist's
   `organization_id` plus its primary `app_artist_organization` link; no
   destructive delete of history across the move.
5. Every state mutation writes an audit entry via the shared
   `AuditRepository` (`app_audit_log`), mirroring the billing package.
6. All natural-key uniqueness (`organization_id`+`normalized_name`,
   `artist_id`+`system_code`) is enforced at the application layer rather
   than via SQL `UNIQUE` indexes — see `data-model.md` "DuckDB known
   limitation" note.

---

## 4. System actors
- **Owner** — full artist.* permission set
- **Administrator** — view/create/update/assign/archive (no transfer)
- **Artist Manager** — view/create/update/assign (no archive/transfer)
- **Artist** — view only (their own org's artists)
- **Viewer** — view only

---

## 5. Related documents
- `plan.md`, `tasks.md`
- `data-model.md`, `business-rules.md`
- `api-contracts.md`, `role-and-permission-model.md`
- `frontend-flows.md`, `test-strategy.md`, `audit-and-security.md`
- `checklist.md`, `traceability.md`
- `evidence/` (m0-setup.md, spec-closure.md, accepted-debt.md)
