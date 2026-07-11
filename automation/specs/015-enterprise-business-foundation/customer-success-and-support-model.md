# Customer Success and Support Model — Spec 015

**Status**: Diseñado  
**Fecha**: 2026-07-11

---

## Customer Success

### Objetivos

Activación, adopción, health, prevención de churn, renovación, expansión.

### Ciclo

```text
onboarding → adopción → health score → riesgo
→ intervención → renovación → expansión
```

### Entidades

`onboarding_step`, `customer_health_snapshot`, (intervenciones como `business_event` / tareas — **diseñado**).

### Health score (**propuesto**)

Composición configurable, p. ej. pesos sobre: login miembros, uso features del plan, mora, tickets abiertos, campañas activas.  
Estados: healthy / watch / risk / critical (máquina de estados).

**No** se publican scores reales inventados.

---

## Soporte

### Ciclo

```text
ticket → clasificación → prioridad → asignación
→ respuesta → escalamiento → resolución → cierre → satisfacción
```

### Entidades

`support_case`, `support_message`.

### Escalamiento

- Técnico → platform_admin  
- Billing → platform_finance / finance org  
- Seguridad/PII → security_admin (BR-SUP-01)

---

## Relación con renovación

CS consume: subscription status, payments overdue, usage, tickets.  
Produce: intervenciones, oportunidades de expansión (hand-off comercial).

---

## Estado actual

Sin CS/support domains en código. Health de **plataforma** (`/health`) ≠ customer health.
