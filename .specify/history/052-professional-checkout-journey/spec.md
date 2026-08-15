# Feature 052 — Professional Subscription and Checkout Journey

**Branch:** `codex/052-professional-checkout-journey`
**Status:** Approved
**Product scope:** Personal and Organization paid subscriptions

## Problem

VOXMETRIKS has plans, subscriptions, invoices, payment attempts and a simulated provider, but the user journeys are disconnected. Personal checkout immediately simulates success, Organization plan selection activates a subscription before payment, and billing screens expose operational actions instead of a coherent purchase flow.

The product must behave like a serious subscription platform while remaining safe for a portfolio environment: payment effects are simulated and clearly disclosed, but state transitions, idempotency, failures, retries, invoices and permissions are real application behavior.

## Product principles

1. No paid subscription becomes active before a successful payment result.
2. A failed or abandoned checkout never removes the currently active subscription.
3. Personal and Organization checkout share one UI/state contract but retain separate domain storage and use cases.
4. Full card number and CVV exist only in browser memory. They are never sent, logged or persisted.
5. The simulated card maps locally to a scenario and sends only safe metadata: brand, last four digits, expiry and an opaque simulation token.
6. Every mutation is tenant-scoped, idempotent and auditable.
7. The interface says “Pago simulado; no se realizará un cargo real” once, clearly, without academic/demo terminology.
8. Existing Billing, Subscriptions and Personal Subscriptions engines are reused. No parallel billing engine is allowed.

## Personas

- **Listener account owner:** purchases or changes a Personal plan and sees the resulting invoice.
- **Organization owner / billing administrator:** creates an organization, selects a paid plan, completes billing data and payment, then enters the operational workspace.
- **Organization member:** may see plan/payment status only when granted the corresponding view capability; cannot mutate checkout.
- **Platform administrator:** can inspect simulated attempts through existing operational surfaces but cannot impersonate a customer checkout.

## Canonical journeys

### Personal

`Plans → Review → Payment method → Confirm → Result → Subscription/Invoice`

- Free remains available without checkout.
- Premium checkout creates a pending checkout, invoice and processing subscription without canceling the current plan.
- Success atomically pays the invoice, activates the selected plan and supersedes the previous paid plan.
- Decline/insufficient funds keeps the checkout retryable and preserves the current plan.
- Processing is resumable after reload.

### Organization

`Create organization → Select plan → Billing profile → Payment method → Confirm → Result → Invite team / Enter workspace`

- Paid selection creates a pending subscription; it does not activate modules.
- Success atomically records payment/allocation, marks the invoice paid, activates the subscription and refreshes module access.
- Failure leaves the organization in onboarding with a clear retry/change-method action.
- Trial activation remains a separate explicit no-charge path and never pretends a payment occurred.

## Simulated card behavior

- Success, decline, insufficient-funds and processing scenarios are selected by documented test card values in the browser.
- The UI performs format/Luhn/expiry validation and immediately discards PAN/CVV after tokenization or navigation.
- Backend requests must reject fields named or shaped as raw PAN/CVV.
- Stored payment methods expose only brand, `last4`, expiry, display label, status and opaque token reference.

## Functional requirements

- **FR-001** Provide resumable checkout sessions with `draft | awaiting_method | ready | processing | succeeded | failed | canceled | expired`.
- **FR-002** Enforce one mutable checkout per scope and target price; repeated idempotency keys replay the same result.
- **FR-003** Validate plan, price, currency and ownership again inside the confirming transaction.
- **FR-004** Keep existing active subscription and entitlements until confirmation succeeds.
- **FR-005** Return server-authoritative `next_action` and never infer activation solely in the frontend.
- **FR-006** Support success, decline, insufficient funds and processing with retry using a new attempt linked to the same checkout.
- **FR-007** Preserve invoice/payment history and never overwrite successful attempts.
- **FR-008** Provide user-facing receipt/result pages and links to subscription and invoice details.
- **FR-009** Refresh session/organization context after activation without logout.
- **FR-010** Apply exact Personal ownership and Organization `subscription.create`, `billing.manage`, `payment.manage` permissions.
- **FR-011** Hide purchase CTAs for view-only users; deep links must return 403 rather than leak another tenant.
- **FR-012** Keep legacy checkout/simulate endpoints as compatibility adapters until their callers are migrated; mark them deprecated in OpenAPI.
- **FR-013** Replace technical IDs/status labels with human controls, summaries and comboboxes while retaining advanced details behind disclosure panels.
- **FR-014** Emit durable audit/subscription events for started, method attached, processing, succeeded, failed, canceled and resumed.
- **FR-015** Automated tests must use isolated DuckDB copies and must not mutate the canonical warehouse.

## Acceptance scenarios

1. Personal success activates the selected plan once and produces one paid invoice on retry/reload.
2. Personal decline preserves the previous plan and can succeed through a new attempt.
3. Organization purchase remains onboarding until payment succeeds, then module access becomes operational without re-login.
4. Organization A cannot view or confirm Organization B checkout, invoice, method or attempt.
5. A view-only member cannot see or invoke checkout mutation controls.
6. Concurrent confirmation of the same checkout produces one payment/allocation/activation.
7. Injected failure at payment, allocation, invoice or activation rolls back the complete confirmation.
8. Browser and backend logs/database contain no raw test PAN or CVV.
9. Desktop 1366×768 and mobile 390×844 complete both success and failure journeys through UI.
10. Free/trial paths remain explicit and create no fake paid invoice.

## Out of scope

- Stripe or another external gateway, webhooks from a real processor or real money movement.
- Tax calculation, exchange rates, proration, coupons and jurisdictional invoicing.
- Artist monetization, royalty settlement and payouts.
- Rewriting existing refund, credit-note, dunning or manual-transfer modules.
- Dashboard/AI changes.
