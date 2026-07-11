# Spec 015 — Deferred decisions

**Fecha:** 2026-07-11  
**Nota:** No bloquean `CLOSED_WITH_DEFERRED_DECISIONS` — la 015 define el modelo, no parámetros finales.

| Decisión | Motivo de aplazamiento | Spec futura responsable (tema) | Riesgo si permanece abierta | Condición para resolver |
|----------|------------------------|--------------------------------|-----------------------------|-------------------------|
| Nombres y límites exactos de planes (Starter/Growth/Enterprise) | Requiere catálogo comercial real | Plans and subscriptions | Confusión comercial si se citan como oficiales | Spec de planes con price book configurable |
| Umbrales de aprobación (descuento, presupuesto, refund) | Números de política org/plataforma | CRM/contracts; Campaigns; Billing | Aprobaciones demasiado laxas/estrictas | Política firmada + config |
| Política trial (días, tarjeta requerida) | Producto/legal comercial | Plans and subscriptions | Activaciones abusivas o fricción | Spec subscriptions |
| Cancelación end-of-term vs immediate (default) | Impacto MRR/UX | Plans and subscriptions + Billing | Disputas de acceso | Spec subscriptions |
| Inclusión de `past_due` en gross_mrr | Definición financiera | Billing / reporting | KPI MRR inconsistente | Spec billing/reporting |
| Provider de pasarela real concreto | Dependencia de vendor/PCI | Billing, payments and reconciliation | Retraso de cobro productivo | Tras mock + decisión vendor |
| Retiro del modo usuario-sin-org | Compatibilidad specs 001–006 | Identity & Organizations (+ follow-up) | Deuda de tenancy dual | Migración membership + feature flags |
| Enmienda constitucional (visión B2B como propósito primario) | Proceso de gobierno | Enmienda Constitución (fuera de 015) | Docs legacy vs 015 | Autorización explícita de enmienda |
| Fórmulas ASC/IFRS de ingreso reconocido | Fuera de alcance v1 | Futuro finance (si aplica) | Confundir cobrado con reconocido | Spec financiera dedicada o mantener OOS |
| Numeración definitiva de specs 016+ | No asignar prematuro | future-specification-map | Colisiones de número | Tras abrir Identity & Organizations |

**Diferidas explícitas de la decisión #10 aprobada:** trial, cancelación, límites de planes, umbrales, fórmulas financieras detalladas.
