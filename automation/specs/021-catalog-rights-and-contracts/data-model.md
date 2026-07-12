# Data Model — Spec 021

## Tables (11)

| Table | Purpose |
|-------|---------|
| `app_catalog_asset` | Org-scoped business catalog asset (song/work) |
| `app_catalog_release` | Org-scoped release record |
| `app_catalog_asset_artist` | Asset ↔ `app_artist_profile` linkage |
| `app_catalog_ownership` | Descriptive admin/label ownership (not % split) |
| `app_rights_contract` | Legal-rights contract (master/publishing/neighboring/other) |
| `app_rights_contract_party` | Party + ownership_percentage per contract |
| `app_rights_territory` | Territory scope per contract |
| `app_rights_authorized_use` | Authorized use codes per contract |
| `app_rights_conflict` | Overlap/conflict records |
| `app_rights_approval` | Submit/approve workflow |
| `app_rights_status_history` | Append-only status trail |

## Distinctions
- **`app_rights_contract`** (this spec) vs **`app_commercial_contract`** (Spec 017 CRM) — separate tables, never joined.
- **`app_catalog_asset`** vs **`dim_track`** — business record optionally linked via `warehouse_track_id`; warehouse never mutated.
- **`app_catalog_ownership`** vs **`app_rights_contract_party`** — descriptive admin link vs legal percentage bookkeeping.

## Key columns
- `app_rights_contract.status`: draft | active | expired | archived | disputed
- `app_rights_contract.rights_type`: master | publishing | neighboring | other
- `app_rights_contract_party.ownership_percentage`: (0, 100] CHECK at SQL layer
- `app_rights_conflict.status`: open | resolved | dismissed
- `app_rights_approval.status`: pending | approved | rejected

## Indexes
Org-scoped lookups on assets, contracts, conflicts; contract_id FK-style indexes on child tables.
