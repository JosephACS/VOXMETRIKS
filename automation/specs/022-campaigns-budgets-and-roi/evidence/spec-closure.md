# Spec Closure — Spec 022 Campaigns, Budgets and ROI

**Final status:** `CLOSED_WITH_ACCEPTED_DEBT`  
**Date:** 2026-07-12

## Summary
Campaign management with budgets, expenses, approvals, attribution, and honest ROI computation delivered. ROI unavailable when prerequisites missing; streams never treated as money.

## Tables delivered (11/11)
`app_campaign`, `app_campaign_objective`, `app_campaign_target`, `app_campaign_budget`, `app_campaign_approval`, `app_campaign_expense`, `app_campaign_result`, `app_attribution_definition`, `app_attributable_revenue_record`, `app_campaign_roi_snapshot`, `app_campaign_status_history`.

## Permissions delivered (6/6)
`campaign.view`, `campaign.create`, `campaign.update`, `campaign.approve`, `campaign.expense`, `campaign.close`.

## Test results
| Suite | Result |
|-------|--------|
| `test_campaigns_schema_o1.py` | **PASS** |
| `test_campaigns_use_cases_o2.py` | **PASS** |
| `test_campaigns_api_o3.py` | **PASS** |
| `test_campaigns_security_o5.py` | **PASS** |
| `campaigns-l4.spec.ts` | service smoke tests present |

## Accepted debt
See `evidence/accepted-debt.md` — Playwright E2E NOT_VERIFIED; no multi-currency FX conversion.
