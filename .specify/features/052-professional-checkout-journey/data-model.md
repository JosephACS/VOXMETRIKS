# Data model — 052 Checkout

## Shared checkout response

The API exposes one structural contract in both contexts while storage remains domain-owned.

```text
CheckoutSession
  id, scope_type, scope_id, actor_user_id
  plan_code, plan_id, plan_price_id, billing_period
  amount, currency
  status, next_action
  subscription_id, invoice_id, payment_attempt_id, payment_method_id
  idempotency_key
  failure_code, created_at, updated_at, expires_at, completed_at
  is_simulated = true
```

## Domain tables

- `personal_checkout_session`: `scope_id` is `user_id`; references Personal plan/price/subscription/invoice/attempt.
- `app_subscription_checkout_session`: `scope_id` is `organization_id`; references Organization plan/price/subscription and Billing invoice/attempt/method.
- `personal_payment_method_reference`: safe Personal token metadata.
- Extend `app_payment_method_reference` only if needed for `brand`, `last4`, `exp_month`, `exp_year`; never store raw card data.

## Invariants

- `(scope_id, idempotency_key)` is unique inside each domain.
- `succeeded` requires paid invoice, succeeded payment attempt and active target subscription.
- `failed/canceled/expired` cannot activate or supersede a subscription.
- A successful attempt is immutable; retry creates a new attempt.
- Exactly one default active method per scope.
- `last4` is exactly four digits; expiry is non-expired at attachment time.
- Unknown/non-applicable values are `NULL`, never synthetic zeroes.

## State transitions

```text
draft → awaiting_method → ready → processing → succeeded
                              ↘ failed → ready (retry/new method)
draft|awaiting_method|ready|failed → canceled
non-terminal + expired_at <= now → expired
```

Illegal transitions return `409 checkout_state_conflict` without mutation.
