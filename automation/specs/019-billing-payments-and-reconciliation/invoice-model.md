# Invoice Model — Spec 019

## Entity: Invoice

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL |
| billing_profile_id | INTEGER | NOT NULL |
| subscription_id | INTEGER | nullable |
| invoice_number | VARCHAR | NOT NULL UNIQUE |
| currency | VARCHAR(3) | NOT NULL |
| status | VARCHAR | draft/issued/partially_paid/paid/past_due/void/partially_credited/credited |
| subtotal | DECIMAL(18,4) | NOT NULL DEFAULT 0 |
| total | DECIMAL(18,4) | NOT NULL DEFAULT 0 |
| amount_paid | DECIMAL(18,4) | NOT NULL DEFAULT 0 |
| amount_due | DECIMAL(18,4) | NOT NULL DEFAULT 0 |
| period_start | DATE | |
| period_end | DATE | |
| due_date | DATE | |
| issued_at | TIMESTAMP | |
| paid_at | TIMESTAMP | |
| voided_at | TIMESTAMP | |
| notes | VARCHAR | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

## Entity: InvoiceItem

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| invoice_id | INTEGER | NOT NULL |
| description | VARCHAR | NOT NULL |
| quantity | DECIMAL(18,4) | NOT NULL DEFAULT 1 |
| unit_price | DECIMAL(18,4) | NOT NULL |
| amount | DECIMAL(18,4) | NOT NULL (quantity × unit_price) |
| period_start | DATE | |
| period_end | DATE | |
| created_at | TIMESTAMP | NOT NULL |

## State machine
```
draft → issued → partially_paid → paid
             ↓              ↓
           void         partially_credited → credited
             ↓
         past_due (overdue)
```

## Rules
- Items immutable after invoice is issued; corrections via credit note
- total = SUM(items.amount)
- amount_due = total - amount_paid
- Voiding a paid invoice requires prior refund
