# Actor and Role Model — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  

Principios: mínimo privilegio · separación de funciones · control por organización · auditoría · aprobaciones sensibles · acceso cross-org **temporal, justificado y auditado**.

Roles técnicos actuales (`user` / engineer / admin) **no se reemplazan** en 015.

---

## A. Roles por organización (cliente)

| Rol | Responsabilidad | Notas |
|-----|-----------------|-------|
| `owner` | Propiedad org; cierre; transferencias | Billing crítico |
| `administrator` | Membresías, config diaria | No bypass audit |
| `billing_manager` | Métodos tokenizados, ver facturas, reintentos | |
| `finance` | Facturas, NC, refunds, conciliación org | |
| `artist_manager` | Roster y derechos operativos | |
| `marketing_manager` | Campañas (con aprobaciones) | |
| `analyst` | KPIs/reportes según plan | |
| `artist` | Visibilidad limitada propia | |
| `viewer` | Solo lectura no sensible | |

Una persona puede tener roles distintos en orgs distintas.

**CRM pre-conversión no es operado por estos roles** (excepto que tras conversión el owner gestione su org).

---

## B. Personal interno de VOXMETRIKS (plataforma)

### Roles de plataforma (operación / control)

| Rol | Responsabilidad |
|-----|-----------------|
| `support_agent` | Tickets; vista org justificada |
| `platform_finance` | Conciliación global; disputes; umbrales |
| `security_admin` | Incidentes, accesos, retención |
| `platform_admin` | Ops, providers, flags |
| `auditor` | Solo lectura + evidencias |

### Roles internos comerciales / CS (**diseñados — añadidos**)

| Rol | Responsabilidad |
|-----|-----------------|
| `sales_agent` | Prospectos, oportunidades, cotizaciones, avance de pipeline |
| `sales_manager` | Aprobaciones comerciales, reopen, coaching pipeline |
| `customer_success_manager` | Onboarding, health, intervenciones, renovación asistida |

Estos roles operan datos **platform-scoped** (CRM) y, con justificación, cuentas cliente post-conversión.

---

## Separación de funciones (ejemplos)

- Aprobar presupuesto campaña ≠ registrar gasto sin control.  
- Emitir credit_note: `finance` / `owner`, no `marketing_manager` ni `sales_agent`.  
- `sales_agent` no es `owner` de la org cliente.  
- Self-approve de descuentos sobre umbral: prohibido.

---

## Mapeo desde roles técnicos actuales

| Actual | Futuro |
|--------|--------|
| Usuario app | identity user; membership org post-migración |
| Admin/engineer técnico | platform_admin / scopes técnicos — **no** sales ni owner cliente |
| Sesión sin org | modo legacy coexistente hasta decisión humana |

---

## Operaciones sensibles (resumen)

| Operación | Roles | Extra |
|-----------|-------|-------|
| Cancelar suscripción | owner, billing_manager | confirmación |
| Reembolso | finance, owner | umbral → platform_finance |
| CRM pre-conversión | sales_agent/manager | no org owner |
| Acceso cross-org | support/CSM/auditor | justificación + audit + temporal |
| Suspender org plataforma | platform_admin/security | ≠ mora |
