# M0 Setup — Spec 021

**Date:** 2026-07-12  
**feature.json:** `automation/specs/021-catalog-rights-and-contracts`

## Preconditions verified
- Spec 020 artists tables (`app_artist_profile`) available for asset/artist linkage
- Spec 017 CRM tables present; `app_commercial_contract` distinct from `app_rights_contract`
- Organizations package with RBAC permission seeding pattern established (016–019)
- Warehouse `dim_track` exists in production ETL; read-only link pattern from Spec 020

## Package scaffold
```
apps/backend/app/packages/catalog_rights/
apps/frontend/src/app/packages/catalog-rights/
automation/specs/021-catalog-rights-and-contracts/
```

## Bootstrap order (main.py)
ensure_user_tables → organizations → … → ensure_artist_tables → **ensure_catalog_rights_tables**
