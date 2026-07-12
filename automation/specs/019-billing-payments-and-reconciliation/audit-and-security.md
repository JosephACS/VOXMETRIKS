# Audit and Security — Spec 019

## Audit trail

All billing use cases write to `app_audit_log` via the existing AuditRepository.

| Event | action value |
|-------|-------------|
| Create billing profile | `billing_profile.created` |
| Issue invoice | `invoice.issued` |
| Void invoice | `invoice.voided` |
| Create payment attempt | `payment_attempt.created` |
| Payment settled | `payment.settled` |
| Payment reconciled | `payment.reconciled` |
| Refund processed | `refund.processed` |
| Credit note created | `credit_note.created` |
| Credit note applied | `credit_note.applied` |
| Ledger entry created | `ledger.entry_created` |

## Security controls

### No PAN/CVV
- `app_payment_method_reference` has NO columns for card numbers, CVV, expiry
- Only `token_ref` (provider opaque token) and `display_label` (masked, e.g. "••••4242")
- Verified by `test_billing_security_l5.py::test_no_pan_cvv_columns`

### Cross-tenant isolation
- All queries filter by `organization_id` from authenticated org context
- Cross-tenant access blocked at dependency layer (X-Organization-Id checked against membership)
- Verified by `test_billing_security_l5.py::test_cross_tenant_blocked`

### Permission enforcement
- billing.view for reads; billing.manage for mutations
- Missing permission → HTTP 403
- Tests verify 403 for unauthorized users

### Provider events
- `/api/v1/billing/provider-events` is the only unauthenticated endpoint
- Protected by `X-Provider-Secret` header (configurable)
- Duplicate events deduplicated by provider_event_id UNIQUE

### Mock provider labeling
- AcademicMockProvider always sets `is_mock: true` in responses
- Clearly labeled `[MOCK]` in display names
- Cannot be used in production (guarded by `provider_code = "academic_mock"`)
