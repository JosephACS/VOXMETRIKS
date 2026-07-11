# I6 — Data validation

**Status**: PASS (honest residual state)  
**Date**: 2026-07-11

## validate_warehouse.py

PASS — facts 900,000; 16 agg tables; DB ~279.8 MB; 29 parquet.

Artifact: `_i6_warehouse_validate.txt`

## Identity / Organizations counts (read-only)

| Table | Count |
|-------|------:|
| app_user | **5** |
| app_session | **269** (+possible +1 from I6 auth smoke login) |
| app_email_code | 0 |
| app_organization | **10** |
| app_organization_member | **12** |
| app_organization_invitation | **4** |
| app_member_role | **12** |
| app_business_role | **9** |
| app_permission | **15** |
| app_role_permission | **48** |
| app_user_organization_preference | **2** |
| app_audit_log | **31** |

Org status: active=9, closed=1.

## Schema DESCRIBE

Documented in `_i6_data_counts.txt` for organization, member, invitation, audit, preference.

## Assertions

| Check | Result |
|-------|--------|
| Identity users unchanged (5) | PASS |
| No automatic org backfill for all users | PASS (users can have 0 orgs) |
| Catalog roles/perms seeded idempotently | PASS (9/15/48) |
| No ELT mutation by 016 | PASS |
| Residual orgs from prior I3/manual use | ACKNOWLEDGED — not deleted |

**No se borraron datos reales** para fabricar estado limpio.
