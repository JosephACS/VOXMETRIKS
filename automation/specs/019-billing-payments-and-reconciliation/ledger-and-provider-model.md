# Ledger and Provider Model — Spec 019

## Entity: BillingLedgerEntry (append-only)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL |
| entry_type | VARCHAR | NOT NULL (invoice_issued/payment_received/refund_issued/credit_note_applied/adjustment) |
| reference_type | VARCHAR | NOT NULL (invoice/payment/refund/credit_note) |
| reference_id | INTEGER | NOT NULL |
| amount | DECIMAL(18,4) | NOT NULL |
| currency | VARCHAR(3) | NOT NULL |
| description | VARCHAR | |
| created_at | TIMESTAMP | NOT NULL |

**APPEND-ONLY**: No UPDATE or DELETE permitted. Violation raises `LedgerImmutableError`.

## Entity: PaymentProviderEvent

Deduplicated webhook store.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| provider_code | VARCHAR | NOT NULL |
| provider_event_id | VARCHAR | NOT NULL UNIQUE |
| event_type | VARCHAR | NOT NULL |
| payload | VARCHAR | JSON blob |
| processed | BOOLEAN | NOT NULL DEFAULT FALSE |
| processed_at | TIMESTAMP | |
| created_at | TIMESTAMP | NOT NULL |

## Entity: PaymentMethodReference

Tokenized refs only — NO PAN/CVV.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PK |
| organization_id | INTEGER | NOT NULL |
| provider_code | VARCHAR | NOT NULL |
| display_label | VARCHAR | NOT NULL (e.g. "••••4242") |
| token_ref | VARCHAR | NOT NULL (provider token, not card number) |
| method_type | VARCHAR | NOT NULL (card/bank_transfer/mock) |
| is_default | BOOLEAN | NOT NULL DEFAULT FALSE |
| status | VARCHAR | active/removed |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

## PaymentProvider interface

```python
class PaymentProvider(Protocol):
    provider_code: str
    display_name: str  # [MOCK] prefix for academic mock

    def initiate_attempt(self, attempt_id: int, amount: Decimal, currency: str, ...) -> ProviderResult: ...
    def confirm(self, attempt_id: int, provider_attempt_id: str) -> ProviderResult: ...
    def refund(self, payment_id: int, amount: Decimal) -> ProviderResult: ...
```

## Providers
- `AcademicMockProvider` — code=`academic_mock`, display=`[MOCK] Academic Payment Provider`
- `ManualTransferRecorder` — code=`manual_transfer`, display=`Manual Bank Transfer`
