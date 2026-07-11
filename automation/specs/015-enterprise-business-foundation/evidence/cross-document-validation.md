# Spec 015 — Cross-document validation

**Fecha:** 2026-07-11  
**Alcance:** 25 documentos Markdown de `015-enterprise-business-foundation/` como un único modelo  
**Resultado:** Sin contradicciones estructurales bloqueantes tras normalización puntual

---

## Inconsistencias encontradas

| ID | Hallazgo | Severidad |
|----|----------|-----------|
| X1 | Nombres de eventos divergentes (`OrgProvisioned` vs Organization*, `ContractSigned` vs ContractAccepted, `PaymentFailed` vs PaymentAttemptFailed, `ArtistCreated`, `RightsDisputed`, `CampaignCompleted`, `ReportReady`) | Media (documental) |
| X2 | `subscription pending` en commercial/self-service (estado inexistente; lifecycle = trialing/active/…) | Media |
| X3 | Alias `CSM` en golden path vs rol canónico `customer_success_manager` | Baja |
| X4 | Decisiones humanas abiertas en traceability previo (ahora aprobadas/diferidas explícitamente) | Proceso |

No se halló: ciclo subscriptions↔billing; mora mutando organization lifecycle; ROI sin fuente; PAN/CVV; CRM pre-conversión por owner org; fórmulas KPI duplicadas conflictivas.

---

## Correcciones realizadas (esta validación)

1. Normalización del **catálogo canónico de eventos** (ver `business-state-machines.md` + docs cruzados).  
2. Eliminación de estado `pending` en suscripción (commercial + operational A-alt).  
3. Alineación de eventos en operational, domain-boundaries, golden-path, billing, commercial.  
4. Registro de decisiones aprobadas/diferidas en `evidence/`.  
5. Cierre documental `CLOSED_WITH_DEFERRED_DECISIONS`.

---

## Procesos validados

| ID | Proceso | Plantilla completa | Estados alineados |
|----|---------|--------------------|-------------------|
| A | Comercial sales-assisted | Sí | Sí |
| A-alt | Self-service | Sí | Sí (sin pending) |
| B–L | Org…Cumplimiento | Sí | Sí |

**Total: 13** procesos/bloques operativos validados.

---

## Máquinas validadas

- 19 máquinas de negocio + access (19b)  
- **130** transiciones documentadas  
- Separación org / subscription / access: **OK**  
- payment_attempt.failed ≠ payment (sin estado failed en payment): **OK**

---

## Entidades validadas

- **54** entidades con sección propia en `data-ownership-model.md`  
- Un dominio propietario cada una  
- Entidades críticas presentes y enlazadas a proceso:  
  `subscription_entitlement`, `payment_provider_event`, `payment_allocation`, `billing_ledger_entry`, `attribution_definition`, `attributable_revenue_record`  
- Sin entidades decorativas sin proceso/regla/KPI

---

## Dominios validados

16 dominios con tablas completas; dependencias acíclicas:

```text
identity → organizations → {crm→contracts, subscriptions→(events)→billing→(events)→orchestration→access,
  artists→catalog_rights→campaigns, customer_success, support, compliance}
engagement → analytics → reporting
platform transversal
```

- subscriptions **no** lee tablas billing  
- CRM pre-conversión **platform-scoped**  
- Post-conversión: `organization_id`

---

## Eventos normalizados (canónicos)

ProspectQualified · OpportunityWon · ContractAccepted · OrganizationProvisioned · SubscriptionActivated · InvoiceIssued · PaymentAttemptFailed · PaymentSettled · PaymentReconciled · AccessLimited · ArtistRegistered · RightsConflictDetected · CampaignApproved · CampaignClosed · ExecutiveReportGenerated · BusinessDecisionRecorded · RenewalCompleted  

(+ OrganizationActivated y auxiliares coherentes)

---

## KPIs validados

- **49** filas KPI-* en `kpi-catalog.md`  
- Columnas uniformes (código, fórmula, fuente, granularidad, frecuencia, propietario, limitaciones, nulos/denom 0, madurez)  
- Distinción logo vs revenue churn; gross vs net MRR; recognized revenue **fuera de alcance v1**  
- ROI = N/D sin atribución; alternativas CMP-02…05

---

## Honestidad de estado

No se presenta como implementado: multi-tenancy org, CRM, billing, pasarela real, derechos, campañas empresariales, CS, soporte empresarial, cumplimiento legal, ROI financiero real.  
Parcial/implementado técnico limitado a identity/auth bearer, analytics/engagement/ELT, audio demo (términos no verificados).
