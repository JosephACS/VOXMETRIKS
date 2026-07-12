# Spec 021 — Catalog Rights and Contracts

**Feature:** Catalog Rights and Contracts
**Status:** CLOSED_WITH_ACCEPTED_DEBT
**Version:** 1.0.0
**Date:** 2026-07-12
**Preceding spec:** 020 Artists and Team Management (CLOSED_WITH_ACCEPTED_DEBT)

---

## 1. Purpose

Deliver organization-scoped **catalog rights and contracts tracking** for
Voxmetriks: a system of record for who owns/controls which rights over a
catalog asset (song/work), in which territories, for how long, and under
what authorized uses — plus conflict detection when claimed ownership
percentages exceed 100% for an overlapping scope.

This is a **rights-tracking tool**, not a legal registry. No screen or
record in this feature asserts or certifies legal validity, ownership, or
enforceability of any right — it reflects only what an organization has
recorded.

- Catalog assets (`app_catalog_asset`) and releases (`app_catalog_release`)
  — business records, optionally linked to the analytics warehouse
  (`dim_track`) and to `app_artist_profile` (Spec 020), never duplicating
  warehouse data
- Rights contracts (`app_rights_contract`) — master/publishing/neighboring/
  other ownership or license records, **distinct from** the CRM's
  commercial (sales) contracts (`app_commercial_contract`, Spec 017)
- Contract parties with ownership percentages, territories, and authorized
  uses
- Percentage validation scoped to (asset, rights_type, territory,
  overlapping period) — never a naive global sum
- Automatic overlap/conflict detection and a manual conflict + resolution
  workflow
- A lightweight submit/approve workflow for contracts
- Append-only status history for contracts

---

## 2. Scope

### In scope
- `app_catalog_asset`, `app_catalog_release`, `app_catalog_asset_artist`,
  `app_catalog_ownership`, `app_rights_contract`,
  `app_rights_contract_party`, `app_rights_territory`,
  `app_rights_authorized_use`, `app_rights_conflict`, `app_rights_approval`,
  `app_rights_status_history` (11 tables)
- Use cases: RegisterCatalogAsset, LinkWarehouseTrack, CreateRelease,
  LinkAssetArtist, CreateRightsContract, AddContractParty, SetTerritories,
  SetAuthorizedUses, SubmitForApproval, ApproveContract, DetectOverlap,
  OpenConflict, ResolveConflict, ArchiveContract, QueryRightsCoverage,
  GetContractHistory (16 use cases, some grouped under shared classes —
  see `traceability.md`)
- Permissions: `rights.view`, `rights.create`, `rights.update`,
  `rights.approve`, `rights.conflict`, `rights.archive`
- REST API under `/api/v1/catalog-rights`
- Frontend package `apps/frontend/src/app/packages/catalog-rights/`

### Out of scope
- Any mutation of `dim_track`/`dim_album` (read-only existence lookup only
  for `LinkWarehouseTrack`; `dim_album` does not exist as a physical table
  in this warehouse, so `warehouse_album_id` is stored as an opaque,
  unvalidated optional reference)
- CRM commercial/sales contracting (`app_commercial_contract`, Spec 017) —
  never joined with `app_rights_contract`
- Royalty calculation/payout (future spec)
- Automatic time-based contract expiry (`valid_to` passing does not
  auto-transition `status` to `expired`; accepted debt)
- Playwright E2E browser verification (NOT_VERIFIED; see
  `evidence/accepted-debt.md`)

---

## 3. Business rules summary
See `business-rules.md` for the full set. Key rules:

1. `app_catalog_asset`/`app_rights_contract` are organization-scoped;
   cross-organization access raises `NotFoundError`.
2. Ownership-percentage validation is **never** a global sum for the whole
   asset. It is computed per `(asset_id, rights_type, territory_code)`
   using a sweep-line algorithm across all non-archived contracts' `[valid_from,
   valid_to]` periods; a territory-less contract is treated as `WORLD`
   scope and overlaps every explicit territory for the same
   asset/rights_type.
3. When the concurrent sum for any tuple exceeds 100%, a
   `rights_conflict` row is opened (or refreshed) and every contract
   contributing to the peak is transitioned to `status='disputed'`.
4. `app_rights_contract` ≠ `app_commercial_contract` — separate tables,
   separate domains, never joined.
5. `warehouse_track_id` is optional and, when set, must reference an
   existing `dim_track.id_track` row; `dim_track` is never mutated.
   `warehouse_album_id` is optional and unvalidated (no `dim_album` table
   exists).
6. Every state mutation writes an audit entry via the shared
   `AuditRepository` (`app_audit_log`), mirroring artists/billing.
7. No destructive DuckDB operations — all schema is idempotent
   `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`.
8. All UI copy avoids asserting legal validity ("recorded", "tracked",
   never "certified"/"legally valid"/"proof of ownership").

---

## 4. System actors
- **Owner** — full `rights.*` permission set
- **Administrator** — view/create/update/approve/conflict/archive
- **Artist Manager** — view/create/update (no approve/conflict/archive)
- **Finance** — view only
- **Viewer** — view only

---

## 5. Related documents
- `plan.md`, `tasks.md`
- `data-model.md`, `business-rules.md`
- `api-contracts.md`, `role-and-permission-model.md`
- `frontend-flows.md`, `test-strategy.md`, `audit-and-security.md`
- `checklist.md`, `traceability.md`
- `evidence/` (m0-setup.md, spec-closure.md, accepted-debt.md)
