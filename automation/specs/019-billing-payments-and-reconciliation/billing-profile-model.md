# Billing Profile Model — Spec 019

## Entity: BillingProfile

One billing profile per organization. Created by billing.manage.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL UNIQUE |
| default_currency | VARCHAR(3) | NOT NULL, ISO-4217 |
| legal_name | VARCHAR | |
| tax_id | VARCHAR | |
| billing_address | VARCHAR | |
| email | VARCHAR | |
| status | VARCHAR | active, suspended, closed |
| created_at | TIMESTAMP | NOT NULL UTC |
| updated_at | TIMESTAMP | NOT NULL UTC |

## Rules
- One profile per org (enforced at use-case level)
- Currency cannot be changed after first invoice issued
- status=suspended blocks new invoice creation
