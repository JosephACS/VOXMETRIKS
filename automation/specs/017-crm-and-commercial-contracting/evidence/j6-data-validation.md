# J6 — Data validation

**Status**: PASS with residual local CRM rows documented

## Warehouse
`validate_warehouse.py` → PASS · facts TOTAL 900,000 · DB ~286 MB

## After ensure_* on `data/warehouse/voxmetrik.duckdb` (2026-07-11)

| Entity | Count |
|--------|------:|
| app_user | 7 |
| app_organization | 10 |
| app_platform_role | 4 |
| app_platform_permission | 17 |
| app_platform_role_permission | 51 |
| app_user_platform_role | 2 |
| app_crm_prospect | 44 |
| app_crm_contact | 4 |
| app_crm_opportunity | 20 |
| app_crm_quotation | 12 |
| app_crm_customer_conversion | 0 |
| app_commercial_contract | 0 |

## Demo CRM users (explicit seed)
`sales_agent_demo` / `sales_agent@voxmetrik.io` · `sales_manager_demo` / `sales_manager@voxmetrik.io`  
Only when demo CRM seed enabled — not silent grant to legacy five users.

## Honest notes
- **No commercial backfill script** ran.
- **No subscription/invoice/payment** tables created.
- Residual CRM prospect/opportunity rows exist in the main warehouse from **local development/API exercise** during 017 implementation. They were **not deleted** (policy: do not destroy data to fabricate cleanliness). They are **not** asserted as production customers/sales.
- Test suites use isolated DuckDB; session pytest DB is separate from warehouse.
- identity users 5→7 explained by two demo sales accounts.
