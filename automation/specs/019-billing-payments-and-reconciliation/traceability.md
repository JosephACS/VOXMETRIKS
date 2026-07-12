# Traceability — Spec 019

## Business objectives → features

| Business Objective | Feature | Spec |
|-------------------|---------|------|
| Monetize subscriptions | Billing profile + invoice lifecycle | 019 |
| Reduce churn on failed payments | past_due / recover orchestration | 019+018 |
| Financial audit compliance | Append-only ledger | 019 |
| PCI-compliance readiness | No PAN/CVV storage | 019 |
| Academic demo | Mock provider ([MOCK]) | 019 |

## Tables → use cases

| Table | Use Cases |
|-------|-----------|
| app_billing_profile | CreateBillingProfile, UpdateBillingProfile |
| app_invoice | IssueInvoice, VoidInvoice, MarkInvoicePastDue |
| app_invoice_item | AddInvoiceItem (within CreateInvoice) |
| app_payment_attempt | CreatePaymentAttempt, RetryPayment |
| app_payment | RecordManualPayment, ConfirmMockPayment, ReconcilePayment |
| app_payment_allocation | AllocatePayment |
| app_refund | RefundPayment |
| app_credit_note | CreateCreditNote, ApplyCreditNote |
| app_payment_provider_event | ProcessProviderEvent |
| app_billing_ledger_entry | (all mutations write ledger entries) |

## API endpoints → use cases

| Endpoint | Use Case |
|----------|---------|
| POST /billing/profile | CreateBillingProfile |
| POST /billing/invoices | CreateInvoice (draft) |
| POST /billing/invoices/{id}/issue | IssueInvoice |
| POST /billing/invoices/{id}/void | VoidInvoice |
| POST /billing/payment-attempts | CreatePaymentAttempt |
| POST /billing/payment-attempts/{id}/confirm | ConfirmMockPayment |
| POST /billing/manual-transfer | RecordManualPayment |
| POST /billing/payments/{id}/allocate | AllocatePayment |
| POST /billing/payments/{id}/reconcile | ReconcilePayment |
| POST /billing/payments/{id}/reverse | ReversePayment |
| POST /billing/refunds | RefundPayment |
| POST /billing/credit-notes | CreateCreditNote |
| POST /billing/credit-notes/{id}/apply | ApplyCreditNote |
| POST /billing/provider-events | ProcessProviderEvent |
| GET /billing/ledger | List ledger entries |

## Dependencies

| Spec | Dependency type |
|------|----------------|
| 016 Identity & Organizations | org membership, auth |
| 017 CRM & Contracts | org permissions pattern |
| 018 Plans & Subscriptions | subscription_id FK, UpdateAccessState |
