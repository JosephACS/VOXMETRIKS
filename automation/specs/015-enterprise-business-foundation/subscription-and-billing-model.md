# Subscription and Billing Model — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  
**Sin implementación de proveedores.**

---

## 1. Fuentes de ingreso (**diseñadas**)

Suscripción mensual/anual · add-ons (artistas, miembros, historial, exports, analytics) · servicios custom (**futuro**).  
Precios **configurables**; no tarifas definitivas.

Planes tentativos Starter / Growth / Enterprise = **propuestos ilustrativos**.

---

## 2. Separación de conceptos financieros

| Concepto | Significado |
|----------|-------------|
| `payment_attempt` | Intento hacia el proveedor (puede fallar) |
| `payment` | Dinero registrado tras attempt exitoso |
| `payment_allocation` | Cuánto de un payment se aplica a cada invoice |
| `refund` | Devolución ligada a un payment |
| `credit_note` | Ajuste documental sobre invoice |
| `billing_ledger_entry` | Asiento append-only; no se edita destructivamente |
| `payment_provider_event` | Evento proveedor con `provider_event_id` único |

---

## 3. Flujo monetario (éxito)

```text
organización
→ plan
→ cotización (sales-assisted) o checkout (self-service)
→ aceptación
→ billing_profile
→ subscription (trialing|active) + entitlements
→ invoice (una moneda = subscription.billing_currency)
→ payment_attempt (idempotency_key)
→ confirmación proveedor / webhook firmado
→ payment + payment_allocation
→ conciliación explícita
→ PaymentSettled → orquestación access full
→ consumo / renovación → RenewalCompleted (si ciclo OK)
```

## 4. Flujo de fallo

```text
payment_attempt.failed → PaymentAttemptFailed
→ notificación
→ reintento (nuevo attempt + nueva idempotency_key o key de reintento definida)
→ subscription.past_due + access.limited (gracia)
→ access.blocked
→ recuperación (PaymentSettled / RenewalCompleted) o cancelación subscription
```

La **organización** no cambia a “past_due”; permanece `active` salvo `suspended_by_platform` / `closed`.

---

## 5. PaymentProvider (abstracción)

`create_payment` · `confirm_payment` · `cancel_payment` · `refund_payment` · `process_webhook`  

Futuro: mock académico · manual · transferencia · pasarela externa. **No implementar en 015.**

---

## 6. Controles financieros obligatorios (diseño)

| Control | Regla |
|---------|-------|
| Idempotencia | `idempotency_key` al crear cobros/attempts |
| Unicidad webhook | `provider_event_id` único; duplicados → ignore (no doble cobro) |
| Firma | verificar firma antes de mutar estado |
| Match | amount + currency attempt = provider = invoice allocation |
| Moneda | invoice no mezcla monedas; subscription tiene `billing_currency` |
| FX | **no** conversión FX en v1 |
| Parciales | solo vía `payment_allocation` |
| Conciliación | proceso explícito → `payment.reconciled` |
| Ledger | append-only; correcciones con refund / credit_note / reversal |
| PCI | no PAN/CVV |

---

## 7. Relación subscriptions ↔ billing

- subscriptions **publica** eventos de ciclo/consumo.  
- billing **consume** eventos y genera documentos/cobros.  
- billing **publica** PaymentSettled / PaymentAttemptFailed / PaymentReconciled.  
- orquestación actualiza entitlements/access.  
- subscriptions **no** lee tablas internas de billing.

---

## 8. Estado vs sistema actual

Cobro SaaS / PaymentProvider / ledger = **Diseñado**. DuckDB no es ledger.
