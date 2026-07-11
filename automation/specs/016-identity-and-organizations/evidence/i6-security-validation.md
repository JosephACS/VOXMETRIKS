# I6 — Security validation

**Status**: PASS (integration) · E2E browser NOT_VERIFIED  
**Date**: 2026-07-11

## Controls verified (pytest I3+I5)

| Control | Evidence |
|---------|----------|
| Deny by default | Non-member → 404; missing perm → 403 |
| Backend authorization | Path context + use-case permission |
| Cross-tenant | Org A ↛ Org B read/patch |
| IDOR | foreign member_id / invitation_id → 404 |
| Tokens not stored plaintext | hash only; list omits token |
| Audit sanitized | no invite_token/token_hash in audit JSON |
| Last owner | leave/revoke blocked |
| Closed/suspended | mutations require active org |
| Preference revalidated | clear on leave/remove; not authz source |
| No admin/engineer org bypass | technical admin ≠ platform operator |
| No PAN/CVV | N/A — no billing |
| No legal compliance claims | none asserted |

## Scope check

No CRM/contracts/subscriptions/billing/payments/enterprise artists/rights/campaigns/CS/support modules implemented under 016.  
Catalog roles `billing_manager` / `marketing_manager` are **RBAC placeholders** with limited org perms only — modules OUT_OF_SCOPE.
