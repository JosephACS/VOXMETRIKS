# Data Model — Spec 020

## Tables

### `app_artist_profile`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| organization_id | INTEGER NOT NULL | owning org |
| display_name | VARCHAR NOT NULL | |
| legal_name | VARCHAR | optional |
| normalized_name | VARCHAR NOT NULL | lowercase, accent-stripped, whitespace-collapsed; app-layer dedupe key with `organization_id` |
| status | VARCHAR NOT NULL DEFAULT 'draft' | draft\|active\|inactive\|archived |
| warehouse_artist_id | INTEGER | optional, non-enforced reference to `dim_artista.id_artista` |
| created_by | INTEGER | |
| created_at / updated_at | TIMESTAMP NOT NULL | |

Indexes: `organization_id`, `normalized_name` (non-unique lookup indexes only).

### `app_artist_organization`
Artist ↔ organization relationship. `id, artist_id, organization_id,
relationship_role (primary|secondary|licensed|partner), is_primary BOOLEAN,
status (active|ended), created_at, updated_at`.
Indexes: `artist_id`, `organization_id`.

### `app_artist_assignment`
Manager assignment. `id, artist_id, organization_id, user_id, role
(default 'manager'), status (active|ended), assigned_at, ended_at,
created_at, updated_at`.
Indexes: `artist_id`, `organization_id`, `user_id`.

### `app_artist_team_member`
General team membership. `id, artist_id, organization_id, user_id,
team_role, status (active|removed), added_at, removed_at, created_at,
updated_at`.
Indexes: `artist_id`, `user_id`.

### `app_artist_external_identifier`
Per-system external id. `id, artist_id, system_code, external_value,
created_at, updated_at`. Uniqueness of `(artist_id, system_code)` enforced
at the application layer (upsert semantics in `SetExternalIdentifier`).
Index: `artist_id`.

### `app_artist_status_history`
Append-only. `id, artist_id, organization_id, from_status, to_status,
reason, actor_user_id, at, created_at`. Index: `artist_id`.

## Status state machine
```
draft --activate--> active
active --deactivate--> inactive
inactive --activate--> active
draft|active|inactive --archive--> archived   (terminal; no further transitions)
```
Enforced in `use_cases.py::_ALLOWED_TRANSITIONS`; anything else raises
`InvalidTransitionError`.

## `app_artist_profile` vs `dim_artista`
`app_artist_profile` is the **business** record (org-scoped, RBAC-governed,
audited). `dim_artista` is the **analytics warehouse** dimension (ELT-owned,
read by streaming/catalog features). The only relationship is the optional,
one-directional `warehouse_artist_id` column — set via `LinkWarehouseArtist`,
which only performs a read-only existence check (`SELECT ... FROM
dim_artista WHERE id_artista = ?`) and never writes to `dim_artista`.

## DuckDB known limitation (uniqueness & UPDATE)
Natural-key uniqueness ((organization_id, normalized_name) on
app_artist_profile; (artist_id, system_code) on
app_artist_external_identifier; (artist_id, organization_id) on
app_artist_organization) is enforced in `use_cases.py` rather than via SQL
`UNIQUE` constraints. DuckDB can, in combination with certain connection
open/close/reopen sequences and/or secondary indexes, raise a spurious
`PRIMARY KEY` `ConstraintException` on `UPDATE` even when no duplicate row
exists (see https://duckdb.org/docs/sql/indexes — "known index
limitations"). `app_artist_profile` field mutations (status transitions,
`LinkWarehouseArtist`, `TransferArtistOrganization`) are therefore applied
via `_update_profile_row()`, an atomic `DELETE` + re-`INSERT` of the same
row (id preserved) instead of a raw `UPDATE`. See
`evidence/accepted-debt.md`.
