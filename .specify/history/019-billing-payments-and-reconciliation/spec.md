> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Spec 019 — Billing, Payments and Reconciliation

**Feature:** Billing, Payments and Reconciliation  
**Status:** CLOSED_WITH_ACCEPTED_DEBT  
**Version:** 1.0.0  
**Date:** 2026-07-11  
**Preceding spec:** 018 Plans and Subscriptions (CLOSED_WITH_ACCEPTED_DEBT)

---

## 1. Purpose

Deliver the full billing lifecycle for Voxmetriks organizations:
- Billing profiles and invoicing per subscription period
- Multi-provider payment processing (Academic Mock Provider + Manual Transfer Recorder)
- Payment allocation and reconciliation
- Refunds and credit notes
- Append-only ledger for audit
- Subscription access-state orchestration (past_due / recover)

---

## 2. Scope

### In scope
- `app_billing_profile` — one per organization, currency anchor
- `app_invoice` / `app_invoice_item` — draft → issued → paid lifecycle; corrections via credit note
- `app_payment_method_reference` — tokenized refs only; **NO PAN/CVV columns**
- `app_payment_attempt` — idempotency_key UNIQUE; states: created/processing/succeeded/failed/canceled
- `app_payment` / `app_payment_allocation` — recorded → settled → reconciled
- `app_refund` / `app_credit_note` — refund against payment; credit note against invoice
- `app_payment_provider_event` — deduplicated webhook store (provider_event_id UNIQUE)
- `app_billing_ledger_entry` — append-only double-entry

### Out of scope
- Real payment processor credentials (no Stripe/PayPal keys)
- PAN, CVV, raw card numbers
- Multi-currency per invoice (one currency per invoice enforced)
- Platform finance role (deferred to 020)

---

## 3. Business rules summary
See `business-rules.md` for full set.

Key rules:
1. One billing profile per organization.
2. Invoice currency must match billing profile default currency.
3. Invoice items immutable after `issued` state; corrections via credit note only.
4. Invoice totals always computed backend (sum of line items).
5. Payment attempt idempotency: duplicate `idempotency_key` → 200 with existing record.
6. Duplicate provider event `provider_event_id` → 200 idempotent.
7. On payment attempt failed + invoice past_due → call `SubscriptionUseCases.update_access_state(also_set_past_due=True)`.
8. On payment settled → recover subscription to active + access full.
9. Ledger entries are append-only; UPDATE/DELETE raise `LedgerImmutableError`.
10. No PAN/CVV columns exist anywhere in schema.

---

## 4. System actors

| Actor | Description |
|-------|-------------|
| org_member (billing.view) | View invoices, payment history |
| org_member (billing.manage) | Create/void invoices, record transfers |
| org_member (invoice.*) | Full invoice lifecycle |
| org_member (payment.*) | Payment operations |
| platform_admin | Break-glass access |
| AcademicMockProvider | Mock payment gateway (clearly labeled) |
| ManualTransferRecorder | Bank-transfer recording |
| SubscriptionOrchestrator | Internal — updates subscription access state |

---

## 5. Key constraints
- DuckDB backend (no foreign key enforcement; logical integrity via use cases)
- All monetary amounts as `DECIMAL(18,4)`
- Timestamps always UTC
- No raw payment credentials stored
