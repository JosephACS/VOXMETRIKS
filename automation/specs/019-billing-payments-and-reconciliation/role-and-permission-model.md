# Role and Permission Model — Spec 019

## New org-scoped permissions

| Code | Description | Domain |
|------|-------------|--------|
| billing.view | View billing profile, invoices, payments, ledger | billing |
| billing.manage | Create/update billing profile, void invoices, record transfers | billing |
| invoice.view | View invoices and items | billing |
| invoice.create | Create and issue invoices | billing |
| invoice.void | Void invoices | billing |
| payment.view | View payments and attempts | billing |
| payment.manage | Initiate, confirm, reconcile payments | billing |
| refund.manage | Process refunds | billing |
| credit_note.manage | Create and apply credit notes | billing |

## Role → permission matrix (019 additions)

| Role | New permissions |
|------|----------------|
| owner | all billing.* + invoice.* + payment.* + refund.manage + credit_note.manage |
| billing_manager | billing.view + billing.manage + invoice.* + payment.* + refund.manage + credit_note.manage |
| finance | billing.view + invoice.view + payment.view |
| administrator | billing.view + invoice.view + payment.view |

## Platform roles (deferred)
- `platform_finance` — DEFERRED to Spec 020
- `platform_admin` — break-glass access via platform RBAC (existing)
