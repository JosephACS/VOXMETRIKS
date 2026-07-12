# Data Validation — Spec 028

**Store:** DuckDB single file — academic limits apply.

## Warehouse (Medallion)

| Layer | Tables | Status |
|-------|--------|--------|
| Dimensions | `dim_*` | **VERIFIED** via ELT + pytest boot data |
| Facts | `fact_streaming` | **VERIFIED** |
| Aggregates | `agg_daily_streams` | **VERIFIED** |
| Control | `ctl_*` | **PARTIAL** — pipeline dependent |

Validation script (optional): `python automation/scripts/validate_warehouse.py`

## Application tables (`app_*`)

| Domain | Table count | Schema tests |
|--------|-------------|--------------|
| Organizations | 6+ | I1 PASS |
| CRM | 8+ | J1 PASS |
| Subscriptions | 10 | K1 PASS |
| Billing | 12+ | L1 PASS |
| Artists | 5+ | M1 PASS |
| Catalog rights | 8+ | N1 PASS |
| Campaigns | 6+ | O1 PASS |
| Business analytics | 4+ | P1 PASS |
| Compliance | 10+ | Q1 PASS |
| Platform ops | 11 | R1 PASS |

## Demo / synthetic labeling

| Mechanism | Status |
|-----------|--------|
| `app_organization.is_demo` column | **IMPLEMENTED** |
| `seed_enterprise_demo.py` marks demo org/plan | **IMPLEMENTED** (opt-in env) |
| Synthetic stats endpoint | **IMPLEMENTED** (engineer-gated) |
| MOCK payment events | **LABELED** academic |

## Integrity rules

- Org-scoped FKs enforced in application layer (DuckDB limited compound UNIQUE)
- Subscription state machine: **VERIFIED** K2
- Billing ledger double-entry pattern: **VERIFIED** L2
- Campaign budget cap: **VERIFIED** O3 (409 on exceed)

## Known data limitations

- No `dim_album` validation for catalog_rights `warehouse_album_id` (021 debt)
- Royalties/payouts tables: **NOT_PRESENT** (024/025 absent)
- Multi-region replication: **OUT_OF_SCOPE**
- DuckDB concurrent writers: serialized via `using_write_conn` lock

## Golden-path data smoke

`test_enterprise_golden_path_s028.py` creates ephemeral org and compliance term — no production warehouse required.
