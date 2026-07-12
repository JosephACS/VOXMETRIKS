# Golden Path Validation — Spec 028 (updated 2026-07-12)

```text
prospect* → opportunity* → quotation* → contract* → organization
→ subscription* → invoice* → payment* → artist* → rights*
→ campaign → KPI → executive report → business decision
→ customer health → support → renewal/expansion
```

`*` = covered primarily by domain suites; smoke chain verifies org→analytics→024→025.

## Automated smoke (`test_enterprise_golden_path_s028.py`)

| Step | Status |
|------|--------|
| Login / org / plans | **VERIFIED** |
| Campaigns / biz-analytics / compliance / platform-ops | **VERIFIED** |
| Report generate + approve + publish + decision | **VERIFIED** (024) |
| Health calculate + support case + resolve + renewal + expansion | **VERIFIED** (025) |
| Legacy `/api/v1/reporting/reports` | optional 404 — canonical `/api/v1/reports` |

## Canonical APIs

- `/api/v1/reports`, `/api/v1/business-decisions`
- `/api/v1/customer-success`, `/api/v1/support`
