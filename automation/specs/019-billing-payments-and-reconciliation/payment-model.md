# Payment Model — Spec 019

## Entity: Payment

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL |
| payment_attempt_id | INTEGER | NOT NULL |
| provider_code | VARCHAR | NOT NULL |
| amount | DECIMAL(18,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| status | VARCHAR | recorded/settled/reconciled/partially_refunded/refunded/reversed |
| provider_payment_id | VARCHAR | nullable |
| settled_at | TIMESTAMP | |
| reconciled_at | TIMESTAMP | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

## Entity: PaymentAllocation

Links a payment to an invoice, allowing partial allocation.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| payment_id | INTEGER | NOT NULL |
| invoice_id | INTEGER | NOT NULL |
| organization_id | INTEGER | NOT NULL |
| amount | DECIMAL(18,4) | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |

## State machine
```
recorded → settled → reconciled
         → partially_refunded → refunded
         → reversed
```

## Rules
- Allocation amount cannot exceed payment.amount
- Sum of allocations cannot exceed invoice.total
- Partial payment: invoice → partially_paid
- Full payment: invoice → paid
