# Business Rules — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
Hereda BR-COM / BR-CRM de 015; amplía para versionado, approvals, conversion.

---

## Heredadas 015 (vigentes)

| ID | Regla | Severidad |
|----|-------|-----------|
| BR-COM-01 | Won requiere quotation accepted (o excepción auditada) | Alta |
| BR-COM-02 | Descuento ≥ umbral → aprobación sales_manager | Alta |
| BR-COM-03 | (015) coherencia pipeline / cotización | Media |
| BR-COM-04 | No convertir / accept quotation expired | Alta |
| BR-CRM-01 | Pre-conversión platform-scoped (sin org_id propietario) | Alta |
| BR-CRM-02 | CRM pre-conversión solo personal plataforma sales_*, no owner cliente | Alta |

---

## Prospect / Contact

| ID | Regla |
|----|-------|
| BR-PRO-01…06 | ver `contact-and-prospect-model.md` |
| BR-CON-01…05 | ver mismo |

## Opportunity / Activity

| ID | Regla |
|----|-------|
| BR-OPP-01…07 | ver `opportunity-pipeline-model.md` |
| BR-ACT-01…05 | ver `sales-activity-model.md` |

## Quotation / Approval / Contract / Conversion

| ID | Regla |
|----|-------|
| BR-QUO-01…08 | quotation-model |
| BR-APR-01…05 | approval-model |
| BR-CTR-01…06 | commercial-contract-model |
| BR-CV-01…09 | customer-conversion-model |

---

## Seguridad / dinero (017)

| ID | Regla |
|----|-------|
| BR-SEC-CRM-01 | Deny by default; sin permiso → 403 |
| BR-SEC-CRM-02 | No bypass por rol técnico admin/engineer |
| BR-SEC-CRM-03 | Tokens invite/org no en audit payloads |
| BR-SEC-CRM-04 | No PAN/CVV en CRM |
| BR-MON-01 | Una moneda por quotation/opportunity/contract alineados |
| BR-MON-02 | Precios propuestos ≠ cobro |
| BR-HON-01 | No afirmar e-sign legal ni compliance |
| BR-HON-02 | Probabilidad ≠ predicción IA |

---

## Umbrales

Valores numéricos exactos = **DEFERRED** (HUM001). Solo claves de configuración referenciadas.
