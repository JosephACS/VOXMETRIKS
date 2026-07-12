# J6 — Backend validation

**Status**: PASS

| Suite | Result |
|-------|--------|
| CRM J1 schema | PASS |
| CRM J2 use cases | PASS |
| CRM J3 API | PASS |
| CRM J5 security | PASS |
| Organizations 016 suites (incl. security) | PASS (no regression) |
| Full pytest | **304 PASS** (0 failed) |

Approx composition: prior ~231 + ~73 CRM.

Startup bootstrap: `ensure_platform_rbac_tables` + `ensure_crm_tables` + `ensure_commercial_contract_tables` before `mark_schema_ready()`.

Auth smoke (identity): covered by existing suites + CRM API login fixtures.
