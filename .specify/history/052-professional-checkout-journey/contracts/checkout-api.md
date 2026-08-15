# API contract — 052 Checkout

All models are strict (`extra=forbid`). Organization endpoints derive tenant from the authenticated organization context.

## Personal

- `POST /api/v1/personal/checkout-sessions`
- `GET /api/v1/personal/checkout-sessions/{checkout_id}`
- `POST /api/v1/personal/checkout-sessions/{checkout_id}/payment-method`
- `POST /api/v1/personal/checkout-sessions/{checkout_id}/confirm`
- `POST /api/v1/personal/checkout-sessions/{checkout_id}/cancel`

## Organization

- `POST /api/v1/subscriptions/checkout-sessions`
- `GET /api/v1/subscriptions/checkout-sessions/{checkout_id}`
- `POST /api/v1/subscriptions/checkout-sessions/{checkout_id}/payment-method`
- `POST /api/v1/subscriptions/checkout-sessions/{checkout_id}/confirm`
- `POST /api/v1/subscriptions/checkout-sessions/{checkout_id}/cancel`

## Create request

```json
{
  "plan_id": 10,
  "plan_price_id": 22,
  "plan_code": "optional-for-personal",
  "billing_period": "monthly",
  "idempotency_key": "client-intent-uuid"
}
```

Only fields applicable to the context are accepted. The server resolves and validates authoritative price/currency.

## Safe payment-method request

```json
{
  "brand": "visa",
  "last4": "4242",
  "exp_month": 12,
  "exp_year": 2030,
  "display_label": "Visa terminada en 4242",
  "simulation_token": "opaque-client-token",
  "is_default": true
}
```

PAN and CVV are not API fields. Requests containing them are rejected with `422`.

## Confirm request

```json
{
  "idempotency_key": "confirm-intent-uuid"
}
```

The scenario is derived from the opaque simulated method token, not supplied as an unrestricted confirmation parameter.

## Response essentials

```json
{
  "id": 101,
  "scope_type": "organization",
  "status": "ready",
  "next_action": "confirm",
  "amount": 49.0,
  "currency": "USD",
  "invoice_id": 88,
  "payment_method": {"brand": "visa", "last4": "4242"},
  "is_simulated": true
}
```

## Stable errors

- `checkout_not_found` — 404
- `checkout_forbidden` — 403
- `checkout_state_conflict` — 409
- `checkout_idempotency_conflict` — 409
- `plan_price_mismatch` — 400
- `payment_method_required` — 400
- `payment_declined` — 402
- `payment_processing` — 202 response state, not an error
- `payment_confirmation_failed` — 409 with rollback
