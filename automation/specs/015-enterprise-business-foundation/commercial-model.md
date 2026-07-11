# Commercial Model — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11

---

## Dos caminos de adquisición

### A. Sales-assisted — **Business Golden Path principal**

Operado por personal interno VOXMETRIKS (`sales_agent`, `sales_manager`), **no** por `owner` de una org cliente.

```text
prospect (platform-scoped)
→ opportunity
→ quotation (plan / precio configurable / add-ons)
→ commercial_contract
→ organization provisioning
→ billing_profile
→ subscription trialing|active
→ invoice / payment
→ activation (entitlements + access)
```

Pre-conversión: **sin `org_id`**. Post-conversión: se relaciona `organization_id`.

### B. Self-service — **camino alternativo**

```text
identity signup
→ organization
→ plan
→ checkout
→ billing_profile
→ subscription (trialing|active)
→ invoice/payment o trial
→ activation
```

Sin pipeline CRM completo; sin `prospect`/`opportunity` obligatorios.

---

## Objetos comerciales (camino A)

| Objeto | Dominio | Scope |
|--------|---------|-------|
| prospect | crm | platform |
| opportunity | crm | platform → +org post |
| quotation | crm | platform |
| commercial_contract | contracts | +org post-firma |

---

## Quién vende / quién compra

| Rol | Función |
|-----|---------|
| Pagador | Organización B2B |
| Vendedor sales-assisted | sales_agent / sales_manager (plataforma) |
| Comprador self-service | persona signup → owner org |

---

## Relación con billing

Tras contrato/`ContractAccepted` + `OrganizationActivated` o checkout: billing_profile → invoice/payment según trial policy.

---

## Estado vs sistema actual

CRM/contracts = **Diseñado**. “Enterprise” analytics actual ≠ comercial.
