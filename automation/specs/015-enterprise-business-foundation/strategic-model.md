# Strategic Model — VOXMETRIKS (Spec 015)

**Status**: Diseñado — metas son **propuestas**, no resultados reales  
**Fecha**: 2026-07-11

Cada objetivo: código, descripción, responsable, KPI, fórmula, fuente, frecuencia, meta propuesta, riesgo, relación táctica.

---

## OE-01 — Aumentar organizaciones activas

| Campo | Valor |
|-------|-------|
| **Descripción** | Crecer la base de organizaciones con suscripción usable |
| **Responsable** | Dirección + Comercial |
| **KPI** | `orgs_active` |
| **Fórmula** | Conteo de organizaciones con `subscription.status ∈ {active, grace}` |
| **Fuente** | Dominio organizations + subscriptions (**futuro**) |
| **Frecuencia** | Mensual |
| **Meta propuesta** | Definir baseline en primera implementación; p. ej. +N% trimestre *(propuesta)* |
| **Riesgo** | Onboarding incompleto → orgs creadas pero inactivas |
| **Tácticos** | OT-COM-01, OT-CS-01, OT-OPS-01 |

---

## OE-02 — Generar ingresos recurrentes

| Campo | Valor |
|-------|-------|
| **Descripción** | Construir MRR/ARR predecible vía planes y add-ons |
| **Responsable** | Finanzas + Comercial |
| **KPI** | `mrr`, `arr` |
| **Fórmula** | MRR = Σ precio_mensualizado de suscripciones activas; ARR = MRR × 12 |
| **Fuente** | subscriptions + plan_price + payments (**futuro**) |
| **Frecuencia** | Mensual |
| **Meta propuesta** | Configurar tras primer plan productivo *(propuesta)* |
| **Riesgo** | Descuentos no gobernados; mora no reflejada |
| **Tácticos** | OT-FIN-01, OT-COM-02, OT-ADM-01 |

---

## OE-03 — Mejorar renovación

| Campo | Valor |
|-------|-------|
| **Descripción** | Maximizar renovaciones y reducir churn voluntario/involuntario |
| **Responsable** | Customer Success + Finanzas |
| **KPI** | `renewal_rate`, `churn_rate` |
| **Fórmula** | Renovación = renovadas / elegibles; Churn = canceladas+expiradas / inicio periodo |
| **Fuente** | subscription_change, CS health (**futuro**) |
| **Frecuencia** | Mensual / trimestral |
| **Meta propuesta** | Umbral de renovación a fijar por dirección *(propuesta)* |
| **Riesgo** | Fallos de pago sin gracia/recuperación |
| **Tácticos** | OT-CS-02, OT-FIN-02, OT-SUP-01 |

---

## OE-04 — Demostrar valor mediante ROI

| Campo | Valor |
|-------|-------|
| **Descripción** | Que campañas y actividad muestren retorno atribuible |
| **Responsable** | Marketing + Datos/Analítica + Dirección |
| **KPI** | `campaign_roi`, `time_to_value` |
| **Fórmula** | ROI = (ingreso_atribuible − gasto) / gasto; TTV = tiempo hasta primer reporte/campaña útil |
| **Fuente** | campaigns + analytics + reporting (**futuro** / analytics **parcial**) |
| **Frecuencia** | Por campaña / mensual |
| **Meta propuesta** | ROI ≥ 0 en campañas cerradas con datos completos *(propuesta)* |
| **Riesgo** | Atribución débil; datos incompletos |
| **Tácticos** | OT-MKT-01, OT-DAT-01, OT-ART-01 |

---

## OE-05 — Aumentar adopción

| Campo | Valor |
|-------|-------|
| **Descripción** | Activar miembros y funciones críticas post-venta |
| **Responsable** | Customer Success + Producto (ops plataforma) |
| **KPI** | `activation_rate`, `wau_org` |
| **Fórmula** | Activación = orgs que completan onboarding_core / orgs nuevas; WAU org = miembros activos / miembros |
| **Fuente** | onboarding_step, audit/business_event, usage (**futuro**) |
| **Frecuencia** | Semanal / mensual |
| **Meta propuesta** | Definir checklist de “primer valor” *(propuesta)* |
| **Riesgo** | Invites sin aceptación; roles mal asignados |
| **Tácticos** | OT-CS-01, OT-ADM-02, OT-OPS-02 |

---

## OE-06 — Garantizar calidad de datos

| Campo | Valor |
|-------|-------|
| **Descripción** | Confiabilidad de warehouse y métricas de negocio |
| **Responsable** | Datos y analítica + Operaciones de plataforma |
| **KPI** | `pipeline_success_rate`, `kpi_freshness` |
| **Fórmula** | Éxitos ELT / ejecuciones; frescura = ahora − last_successful_load |
| **Fuente** | ctl_* / validate_warehouse (**parcial** actual) + business KPIs (**futuro**) |
| **Frecuencia** | Diaria |
| **Meta propuesta** | 0 fallos silenciosos en carga crítica *(propuesta)* |
| **Riesgo** | Confundir métricas demo con KPIs SaaS |
| **Tácticos** | OT-DAT-02, OT-OPS-03 |

---

## OE-07 — Proteger información empresarial

| Campo | Valor |
|-------|-------|
| **Descripción** | Acceso mínimo, auditoría, consentimientos, incidentes |
| **Responsable** | Seguridad y cumplimiento + platform_admin |
| **KPI** | `sensitive_access_audited`, `incident_mttr` |
| **Fórmula** | % accesos sensibles con audit_log; MTTR = resolución − detección |
| **Fuente** | compliance + audit_log (**futuro** / auth **parcial**) |
| **Frecuencia** | Mensual |
| **Meta propuesta** | 100% operaciones sensibles auditadas *(propuesta)* |
| **Riesgo** | Roles técnicos actuales demasiado amplios |
| **Tácticos** | OT-SEC-01, OT-SEC-02 |

---

## OE-08 — Mantener sostenibilidad operativa

| Campo | Valor |
|-------|-------|
| **Descripción** | Operar la plataforma con costo y calidad sostenibles |
| **Responsable** | Operaciones de plataforma + Administración |
| **KPI** | `availability`, `support_backlog_age` |
| **Fórmula** | Disponibilidad = uptime / periodo; edad media tickets abiertos |
| **Fuente** | health/ops (**parcial**) + support (**futuro**) |
| **Frecuencia** | Semanal |
| **Meta propuesta** | SLA internos a definir *(propuesta)* |
| **Riesgo** | Deuda 014 (Docker/Playwright) sin cerrar operacionalmente |
| **Tácticos** | OT-OPS-01, OT-SUP-02, OT-ADM-03 |

---

## Mapa estratégico → táctico (resumen)

| OE | Áreas tácticas primarias |
|----|--------------------------|
| OE-01 | Comercial, CS, Ops |
| OE-02 | Finanzas, Comercial, Administración |
| OE-03 | CS, Finanzas, Soporte |
| OE-04 | Marketing, Datos, Gestión artística |
| OE-05 | CS, Administración, Ops |
| OE-06 | Datos, Ops |
| OE-07 | Seguridad |
| OE-08 | Ops, Soporte, Administración |
