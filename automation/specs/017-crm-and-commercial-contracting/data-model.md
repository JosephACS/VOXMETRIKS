# Data Model (conceptual) — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Sin SQL.** Naming físico propuesto bajo convención `app_*` — **confirmar HUM002 antes de D1**.

---

## Convención de nombres propuesta

| Conceptual | Tabla física propuesta | Dominio owner |
|------------|------------------------|---------------|
| crm_prospect | `app_crm_prospect` | crm |
| crm_contact | `app_crm_contact` | crm |
| crm_prospect_contact | `app_crm_prospect_contact` | crm |
| crm_opportunity | `app_crm_opportunity` | crm |
| crm_opportunity_stage_history | `app_crm_opportunity_stage_history` | crm |
| crm_sales_activity | `app_crm_sales_activity` | crm |
| crm_quotation | `app_crm_quotation` | crm |
| crm_quotation_version | `app_crm_quotation_version` | crm |
| crm_quotation_item | `app_crm_quotation_item` | crm |
| crm_approval_request | `app_crm_approval_request` | crm |
| crm_commercial_contract | `app_crm_commercial_contract` | crm *(capacidad 017; 015 decía dominio contracts)* |
| crm_customer_conversion | `app_crm_customer_conversion` | crm |
| crm_audit_reference | `app_crm_audit_event` **o** reutilizar `app_organization_audit`-style / audit global | crm |

**Alternativa:** `app_commercial_contract` sin prefijo crm — decisión HUM007/HUM002.

---

## Fichas por entidad

Plantilla: owner · scope · PK · relaciones · estados · restricciones · auditoría · retención · sensibilidad · proceso · KPI.

### app_crm_prospect
| Campo | Valor |
|-------|-------|
| Owner | crm |
| Scope | platform; `organization_id` null→set post |
| PK | prospect_id |
| Rel | contacts N:N; opportunities 1:N |
| Estados | lead/new…converted |
| Restricciones | owner_user_id sales; no merge auto |
| Audit | create/update/status |
| Retención | comercial |
| Sensibilidad | media (PII) |
| Proceso | A |
| KPI | prospects_created, qualification_rate |

### app_crm_contact
| Campo | Valor |
|-------|-------|
| Owner | crm |
| Scope | platform |
| PK | contact_id |
| Rel | prospects N:N; optional linked_user_id → app_user |
| Estados | n/a (flags) |
| Restricciones | email unique soft; no auto user |
| Audit | sí |
| Retención | comercial/PII policy |
| Sensibilidad | alta (email/phone) |
| Proceso | A |
| KPI | — |

### app_crm_prospect_contact
PK compuesto prospect_id+contact_id · flags primary/decision/signatory.

### app_crm_opportunity
Scope platform→+org · PK opportunity_id · FK prospect · expected_value+currency · estados pipeline · KPI pipeline/win/loss/cycle.

### app_crm_opportunity_stage_history
Append-only · FK opportunity · from/to · actor · at.

### app_crm_sales_activity
FK al menos uno prospect/contact/opportunity · tipos · audit.

### app_crm_quotation / _version / _item
Moneda única · version immutability · plan_code conceptual · KPI acceptance/discount.

### app_crm_approval_request
object_type/id · threshold_ref · statuses · audit decisions.

### app_crm_commercial_contract
FK quotation accepted · legal name · signatory · acceptance_evidence · ≠ subscription.

### app_crm_customer_conversion
unique opportunity_id · idempotency_key · org link · status saga.

### Audit reference
Cada mutación sensible → evento audit (quién, qué, entity ids, before/after sanitized).

---

## Índices lógicos (no SQL)

- prospect status + owner  
- opportunity status + owner + expected_close  
- quotation opportunity + status  
- approval pending + approver role  
- conversion opportunity unique  
- contact email normalized  

---

## Prohibido en modelo 017

Tablas invoice, payment, subscription, billing_profile, campaign, rights_contract.
