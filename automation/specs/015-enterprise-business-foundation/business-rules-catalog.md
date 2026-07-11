# Business Rules Catalog — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  
Estado de enforcement B2B: **Diseñado** (no en código).

---

## Comercial / CRM

| ID | Regla | Severidad |
|----|-------|-----------|
| BR-COM-01 | Won requiere quotation accepted o excepción auditada | Alta |
| BR-COM-02 | Descuento ≥ umbral → sales_manager / platform_finance | Alta |
| BR-COM-03 | Lost exige razón codificada | Media |
| BR-COM-04 | No convertir quotation expired | Alta |
| BR-CRM-01 | Prospect/opportunity pre-conversión platform-scoped (sin org_id) | Alta |
| BR-CRM-02 | CRM pre-conversión solo personal plataforma (sales_*), no owner cliente | Alta |

## Organización

| ID | Regla |
|----|-------|
| BR-ORG-01 | Mutaciones sensibles requieren membership active |
| BR-ORG-02 | ≥1 owner active |
| BR-ORG-03 | Invite no aceptada ≠ permisos |
| BR-ORG-04 | suspended_by_platform / closed bloquea writes no-plataforma |
| BR-ORG-05 | Mora no cambia organization.status; usa subscription/access |

## Suscripción

| ID | Regla |
|----|-------|
| BR-SUB-01 | Features ⊆ entitlements activos |
| BR-SUB-02 | Trial no factura salvo política |
| BR-SUB-03 | Cancelación respeta end-of-term vs immediate |
| BR-SUB-04 | Todo cambio → subscription_change |
| BR-SUB-05 | Una billing_currency por subscription |
| BR-SUB-06 | No FX en v1 |
| BR-SUB-07 | No leer tablas internas billing |
| BR-SUB-08 | past_due dispara access limited/blocked vía orquestación |

## Facturación

| ID | Regla |
|----|-------|
| BR-BILL-01 | No emitir sin billing_profile completo |
| BR-BILL-02 | Impuestos configurables (no jurisdicción afirmada) |
| BR-BILL-03 | Void solo estados permitidos |
| BR-BILL-04 | Credit note ≤ elegible |
| BR-BILL-05 | Invoice una sola moneda |
| BR-BILL-06 | Ledger append-only |
| BR-BILL-07 | Correcciones vía refund / credit_note / reversal |
| BR-BILL-08 | Conciliación es proceso explícito |
| BR-BILL-09 | Pagos parciales vía payment_allocation |

## Pagos

| ID | Regla |
|----|-------|
| BR-PAY-01 | Prohibido PAN/CVV |
| BR-PAY-02 | Solo payment_method_reference / tokens |
| BR-PAY-03 | Webhook con verificación de firma |
| BR-PAY-04 | Cadena rechazo→reintento→gracia→limited→blocked→recover/cancel |
| BR-PAY-05 | Refund ligado a payment |
| BR-PAY-06 | idempotency_key al crear cobros/attempts |
| BR-PAY-07 | provider_event_id único; duplicado no doble cobro |
| BR-PAY-08 | amount+currency deben coincidir attempt/provider/allocation |
| BR-PAY-09 | failed pertenece a payment_attempt, no a payment |
| BR-PAY-10 | payment solo desde attempt succeeded |
| BR-PAY-11 | No auto-reconcile sin proceso |
| BR-PAY-12 | payment ≠ allocation ≠ refund ≠ credit_note ≠ ledger_entry |

## Artistas / catálogo

| ID | Regla |
|----|-------|
| BR-ART-01 | Artista vía assignment a org |
| BR-ART-02 | No usar dim_artista como SoT legal |
| BR-CAT-01 | Campaña requiere rights approved+vigente |
| BR-CAT-02 | Validar 100% por asset + rights_type + territory + periodo |
| BR-CAT-03 | disputed bloquea nuevos usos |
| BR-CAT-04 | rights_contract incluye exclusive/non-exclusive + authorized_use |
| BR-CAT-05 | valid_from/valid_to obligatorios para active |
| BR-CAT-06 | contract_party.ownership_percentage coherente en el slice |

## Campañas

| ID | Regla |
|----|-------|
| BR-CMP-01 | Gasto ≤ presupuesto aprobado salvo change request |
| BR-CMP-02 | Umbral → dual approval |
| BR-CMP-03 | Cierre exige resultado o justificación |
| BR-CMP-04 | ROI solo si fuente ingreso + moneda + periodo + attribution_definition + versión + confianza + aprobador |
| BR-CMP-05 | gasto=0 o sin ingreso atribuible → ROI No disponible |
| BR-CMP-06 | No convertir streams en dinero sin fuente aprobada |

## CS / Soporte / Cumplimiento / Analítica

| ID | Regla |
|----|-------|
| BR-CS-01 | health critical → intervención |
| BR-CS-02 | Acceso CS cross-org temporal, justificado, auditado |
| BR-SUP-01 | Escalate security si PII/breach |
| BR-SUP-02 | CSAT al cierre si configurado |
| BR-CMPL-01 | Cross-org plataforma con justificación + audit |
| BR-CMPL-02 | Eliminación respeta retención configurable |
| BR-CMPL-03 | Consentimiento antes de finalidades de marketing procesadas |
| BR-AN-01 | No publicar KPI oficial si freshness fuera de SLA |
| BR-AN-02 | No mezclar demo/warehouse con MRR sin etiquetar |
