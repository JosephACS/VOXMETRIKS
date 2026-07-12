# API Contracts — Spec 019

All endpoints under `/api/v1/billing`. Auth via Bearer token. Org context via `X-Organization-Id` header.

## Billing Profile
```
GET    /api/v1/billing/profile                    billing.view
POST   /api/v1/billing/profile                    billing.manage (create)
PATCH  /api/v1/billing/profile                    billing.manage (update)
```

## Invoices
```
GET    /api/v1/billing/invoices                   invoice.view
POST   /api/v1/billing/invoices                   invoice.create
GET    /api/v1/billing/invoices/{id}              invoice.view
POST   /api/v1/billing/invoices/{id}/issue        invoice.create
POST   /api/v1/billing/invoices/{id}/void         invoice.void
GET    /api/v1/billing/invoices/{id}/items        invoice.view
```

## Payment Attempts
```
GET    /api/v1/billing/payment-attempts           payment.view
POST   /api/v1/billing/payment-attempts           payment.manage
GET    /api/v1/billing/payment-attempts/{id}      payment.view
POST   /api/v1/billing/payment-attempts/{id}/confirm   payment.manage
POST   /api/v1/billing/payment-attempts/{id}/cancel    payment.manage
```

## Payments
```
GET    /api/v1/billing/payments                   payment.view
GET    /api/v1/billing/payments/{id}              payment.view
POST   /api/v1/billing/payments/{id}/settle       payment.manage
POST   /api/v1/billing/payments/{id}/reconcile    payment.manage
POST   /api/v1/billing/payments/{id}/allocate     payment.manage
POST   /api/v1/billing/payments/{id}/reverse      payment.manage
```

## Manual Transfer
```
POST   /api/v1/billing/manual-transfer            payment.manage
```

## Refunds
```
GET    /api/v1/billing/refunds                    payment.view
POST   /api/v1/billing/refunds                    refund.manage
GET    /api/v1/billing/refunds/{id}               payment.view
```

## Credit Notes
```
GET    /api/v1/billing/credit-notes               invoice.view
POST   /api/v1/billing/credit-notes               credit_note.manage
GET    /api/v1/billing/credit-notes/{id}          invoice.view
POST   /api/v1/billing/credit-notes/{id}/apply    credit_note.manage
```

## Ledger
```
GET    /api/v1/billing/ledger                     billing.view
```

## Provider Events (webhook receiver)
```
POST   /api/v1/billing/provider-events            (no auth — provider secret header)
```

## Payment Method References
```
GET    /api/v1/billing/payment-methods            billing.view
POST   /api/v1/billing/payment-methods            billing.manage
DELETE /api/v1/billing/payment-methods/{id}       billing.manage
```

## Standard response envelope
```json
{ "id": 1, "status": "issued", ... }          // resource
{ "items": [...], "total": 10, "page": 1 }    // paginated list
{ "message": "...", "code": "..." }           // error
```
