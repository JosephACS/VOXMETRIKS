# Refund and Credit Note Model — Spec 019

## Entity: Refund

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL |
| payment_id | INTEGER | NOT NULL |
| amount | DECIMAL(18,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| reason | VARCHAR | |
| status | VARCHAR | pending/processed/failed |
| processed_at | TIMESTAMP | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

## Entity: CreditNote

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL |
| invoice_id | INTEGER | NOT NULL (original invoice being credited) |
| credit_note_number | VARCHAR | NOT NULL UNIQUE |
| amount | DECIMAL(18,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| reason | VARCHAR | |
| status | VARCHAR | draft/issued/applied/voided |
| issued_at | TIMESTAMP | |
| applied_at | TIMESTAMP | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

## Rules
- Refund amount ≤ payment amount
- Credit note amount ≤ invoice total
- Credit note application adjusts invoice amount_paid and status
- Credit note is the only mechanism for correcting issued/paid invoice items
