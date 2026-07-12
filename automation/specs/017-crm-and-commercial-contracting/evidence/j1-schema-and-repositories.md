# J1 — Schema and repositories

**Status**: PASS

## Tables created (bootstrap APP)

### Platform RBAC
`app_platform_role` · `app_platform_permission` · `app_platform_role_permission` · `app_user_platform_role`

### CRM
`app_crm_prospect` · `app_crm_contact` · `app_crm_prospect_contact` · `app_crm_opportunity` · `app_crm_opportunity_stage_history` · `app_crm_sales_activity` · `app_crm_quotation` · `app_crm_quotation_version` · `app_crm_quotation_item` · `app_crm_approval_request` · `app_crm_customer_conversion`

### Contracts
`app_commercial_contract`

### Reused
`app_audit_log` (organization_id nullable; sources `crm.use_case` / `contracts.use_case`)

## Properties
CREATE IF NOT EXISTS · additive · idempotent · wired in `main.py` before `mark_schema_ready()` · no warehouse regenerate · no subscription/invoice/payment/billing/campaign/rights tables

## Packages
- `apps/backend/app/packages/platform_rbac/`
- `apps/backend/app/packages/crm/` (schema + use cases act as persistence layer)
- `apps/backend/app/packages/contracts/` (schema + repository)

## Tests
`test_crm_schema_j1.py` — PASS (schema_ready gate reset in fixtures for full-suite isolation)
