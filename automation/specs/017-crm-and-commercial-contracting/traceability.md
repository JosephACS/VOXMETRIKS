# Traceability — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
Cadena: objetivo 015 → capacidad 017 → proceso → actor → CU → regla → estado → entidad → (repo/API/UI/test **futuros**).

---

## Mapa capacidad

| Eslabón | Artefacto |
|---------|-----------|
| Objetivo 015 | sales-assisted golden path A |
| Capacidad | CRM & commercial contracting (017) |
| Proceso | operational-model A (015) + docs 017 |
| Actores | role-and-permission-model.md |
| Casos uso | spec.md US1–US8 |
| Reglas | business-rules.md |
| Estados | lifecycle-state-machines.md |
| Entidades | data-model.md |
| Repositorio | FUTURO D1 |
| Endpoint | api-contracts.md (diseñado) |
| Pantalla | frontend-flows.md (diseñado) |
| Permiso | role-and-permission-model.md |
| Prueba | test-strategy.md (diseñado) |
| Evidencia | FUTURO D6 |

---

## Trazabilidad US → docs

| US | Modelos | API | UI | Tests |
|----|---------|-----|----|-------|
| US1 Prospect/Contact | contact-and-prospect | /crm/prospects, contacts | list/detail | scope, duplicates |
| US2 Opportunity | opportunity-pipeline | /crm/opportunities | board | transitions |
| US3 Activities | sales-activity | /crm/activities | timeline | no email send |
| US4 Quotation | quotation-model | /crm/quotations | editor | version immutability |
| US5 Approval | approval-model | /crm/approvals | inbox | separation of duties |
| US6 Contract | commercial-contract | /crm/contracts | detail | accept evidence |
| US7 Conversion | customer-conversion | /crm/conversions | wizard | idempotency, org |
| US8 Audit/isolation | audit-and-security | /crm/audit | audit | 403 org user |

---

## KPIs (propuestos — sin resultados)

| KPI | Fórmula | Fuente | Freq | Owner | Limitación | null/zero | Madurez |
|-----|---------|--------|------|-------|------------|-----------|---------|
| prospects_created | count prospects created | crm_prospect | M | sales_manager | solo CRM | 0 válido | Propuesto |
| qualification_rate | qualified / (qualified+disqualified) | prospect | M | sales_manager | excluye open | denom=0 → N/D | Propuesto |
| pipeline_value | Σ expected_value open stages | opportunity | M | sales_manager | estimates | null excluir | Propuesto |
| opportunities_by_stage | count group by status | opportunity | W/M | sales_agent | — | 0 válido | Propuesto |
| win_rate | won / (won+lost) | opportunity | M | sales_manager | ignora canceled policy | denom=0 → N/D | Propuesto (=KPI-COM-01) |
| loss_rate | lost / (won+lost) | opportunity | M | sales_manager | idem | N/D | Propuesto |
| average_sales_cycle | avg(won_at−created_at) | opportunity | M | sales_manager | solo won | sin fechas excluir | Propuesto (=KPI-COM-03) |
| quote_acceptance_rate | accepted / sent | quotation | M | sales_manager | versions | N/D | Propuesto |
| discount_rate | avg discount on accepted | quotation_version | M | sales_manager | umbral config | null→excluir | Propuesto |
| conversion_time | avg(converted_at−contract.accepted_at) | conversion | M | sales_manager | solo succeeded | N/D | Propuesto |
| contracts_accepted | count accepted | contract | M | sales_manager | — | 0 válido | Propuesto |

Alineados a KPI-COM-01…05 de 015 donde aplica; ampliados sin inventar series.

---

## Gaps conscientes (OK en borrador)

- Repo/endpoint/UI/test **sin implementación** — marcados diseñados.  
- Umbrales numéricos DEFERRED.  
- feature.json aún 016.

## Anti-gaps (no deben ocurrir en diseño)

- Endpoint sin US/permiso — revisado en api-contracts.  
- Pantalla sin API — frontend-flows.  
- Tabla sin proceso — data-model.  
- Regla sin prueba futura — test-strategy.  
- Billing colado — OUT explícito.
