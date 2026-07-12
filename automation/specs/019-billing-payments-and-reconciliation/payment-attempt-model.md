# Payment Attempt Model — Spec 019

## Entity: PaymentAttempt

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL |
| invoice_id | INTEGER | NOT NULL |
| payment_method_ref_id | INTEGER | nullable |
| provider_code | VARCHAR | NOT NULL (academic_mock / manual_transfer) |
| idempotency_key | VARCHAR | NOT NULL UNIQUE |
| amount | DECIMAL(18,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| status | VARCHAR | created/processing/succeeded/failed/canceled |
| provider_attempt_id | VARCHAR | nullable (provider reference) |
| failure_reason | VARCHAR | nullable |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

## State machine
```
created → processing → succeeded → (creates Payment record)
                    ↓
                  failed → (can retry → creates new attempt)
created → canceled
```

## Idempotency
- Same idempotency_key → return existing record, 200 OK
- Different idempotency_key, same invoice → new attempt allowed if previous is failed/canceled

## Providers
- `academic_mock` — [MOCK] deterministic success/failure based on amount
- `manual_transfer` — bank wire reference, succeeds when manually confirmed
