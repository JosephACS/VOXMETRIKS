# Customer Conversion Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Depende de:** Organizations 016 (create / link / invite / owner).

---

## Objetivo

Pasar de cuenta CRM a **organización cliente** sin cobrar ni activar plan.

```text
opportunity = won (o winning path)
+ quotation = accepted
+ contract = accepted
→ ConvertCustomer (idempotent)
   → create OR link organization (016)
   → ensure owner (membership o invitation 016)
   → write crm_customer_conversion
   → set organization_id on prospect/opportunity/contract
   → prospect = converted
   → contract = active_handoff
   → emit CustomerConverted
→ handoff payload futuro a subscriptions (NO ejecutar en 017)
```

---

## crm_customer_conversion

### Campos
`conversion_id` · `opportunity_id` (unique) · `contract_id` · `prospect_id` · `organization_id` · `mode` (`create_org` | `link_existing`) · `owner_user_id?` · `invitation_id?` · `idempotency_key` · `status` (`started`|`succeeded`|`failed`|`compensating`) · `error_code?` · `converted_at?` · `converted_by` · timestamps

---

## Saga local / atomicidad lógica

| Paso | Si falla |
|------|----------|
| Validar precondiciones | abort; no side effects |
| Create/link org vía Organizations | no conversion row succeeded |
| Owner / invite | rollback lógico o compensating; **no** org active sin owner (invariante 016) |
| Persistir conversion + links | retry idempotent |
| Emit event | after durable success |

DuckDB: misma honestidad 016 — transacción lógica + tests; no ACID distribuido real.

---

## Reglas

| ID | Regla |
|----|-------|
| BR-CV-01 | No doble conversión misma opportunity (`unique`) |
| BR-CV-02 | No crear organizaciones duplicadas silenciosamente — detectar slug/legal_name/link explícito |
| BR-CV-03 | No org sin owner (016) |
| BR-CV-04 | Si contacto sin `linked_user_id` → invitación 016 al email del signatory/primary |
| BR-CV-05 | Preservar historial CRM (no borrar prospect/opportunity) |
| BR-CV-06 | Idempotency-Key en API convert |
| BR-CV-07 | Permiso `customer.convert` |
| BR-CV-08 | No activar subscription/billing |
| BR-CV-09 | Usuarios org-cliente no ejecutan convert sobre CRM ajeno |

---

## Modos

| Mode | Cuándo |
|------|--------|
| `create_org` | No existe org cliente |
| `link_existing` | Org ya existe (p.ej. creada manualmente en 016); requiere confirmación humana anti-link erróneo |

---

## Salida hacia subscriptions (futuro)

Evento `CustomerConverted` con: organization_id, contract_id, quotation terms_snapshot, currency, plan_code refs.  
Consumidor futuro: Plans & Subscriptions — **OUT 017**.
