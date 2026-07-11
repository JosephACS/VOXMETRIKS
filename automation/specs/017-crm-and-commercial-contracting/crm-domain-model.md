# CRM Domain Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Dominio propietario (capacidad):** `crm` (+ `commercial_contract` en esta spec)  
**Scope pre-conversión:** **platform** (sin `organization_id` como propietario)  
**Scope post-conversión:** entidades CRM conservan historial y pueden **referenciar** `organization_id`.

---

## Visión

CRM interno operado por personal VOXMETRIKS (`sales_agent`, `sales_manager`). No es el portal del cliente organización.

```text
[Platform sales users]
        │
        ▼
  crm_prospect ── contacts
        │
        ▼
  crm_opportunity ── activities · stage_history
        │
        ▼
  crm_quotation (+ versions/items) ── approval_request
        │
        ▼
  crm_commercial_contract
        │
        ▼
  crm_customer_conversion ──► Organizations (016)
        │
        ▼
  CustomerConverted (handoff futuro → subscriptions)  [OUT implementar]
```

---

## Agregados conceptuales

| Agregado | Raíz | Incluye |
|----------|------|---------|
| ProspectAggregate | prospect | contacts links, status |
| OpportunityAggregate | opportunity | stage history, activities refs, owner |
| QuotationAggregate | quotation | versions, items, discounts |
| ApprovalAggregate | approval_request | decisions |
| ContractAggregate | commercial_contract | acceptance evidence |
| ConversionAggregate | customer_conversion | org link, idempotency |

---

## Bounded context rules

| Regla | Detalle |
|-------|---------|
| Un solo owner de escritura CRM | package/dominio crm |
| Org write | solo vía puerto Organizations en conversión |
| Plan catalog | **read conceptual** futuro; no mutar subscriptions |
| Billing | **prohibido** write |
| Rights contract | dominio distinto — no mezclar |

---

## Eventos de dominio (diseñados)

`ProspectCreated` · `ProspectContacted` · `ProspectQualified` · `ProspectDisqualified` · `ProspectConverted`  
`OpportunityOpened` · `OpportunityStageChanged` · `OpportunityWon` · `OpportunityLost` · `OpportunityCanceled`  
`ActivityRecorded`  
`QuotationVersionCreated` · `QuotationSent` · `QuotationAccepted` · `QuotationRejected` · `QuotationExpired` · `QuotationSuperseded`  
`ApprovalRequested` · `ApprovalDecided`  
`ContractSubmitted` · `ContractApproved` · `ContractSent` · `ContractAccepted` · `ContractRejected` · `ContractExpired` · `ContractTerminated`  
`CustomerConverted` · `OrganizationLinkedFromCrm`

---

## Relación con KPIs

Ver KPIs en `traceability.md` / sección KPI de este set: pipeline value, win/loss, cycle, quote acceptance, conversion time — todos **Propuestos**, sin series inventadas.

---

## Honestidad

Ningún agregado existe en código. Assessment: `current-system-assessment.md`.
