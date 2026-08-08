> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Identity and Organizations

**Feature Branch**: `016-identity-and-organizations` *(propuesta; Git manual)*  
**Feature Directory**: `.specify/history/016-identity-and-organizations/`  
**Created**: 2026-07-11  
**Status**: **DESIGN_APPROVED** (validación cruzada 2026-07-11) — **IMPLEMENTATION_COMPLETE** · **CLOSED_WITH_ACCEPTED_DEBT** (I6 2026-07-11)  
**Input**: Primera spec de implementación aprobada tras 015 — base multi-organización reutilizando identity existente.  
**Readiness:** CLOSED. **I0–I6 COMPLETE**. Playwright E2E = NOT_VERIFIED (accepted debt).

**Número de spec:** **016** (disponible tras 015-enterprise-business-foundation).

**Prerrequisitos:** Constitución v2.0.0; spec 015 `CLOSED_WITH_DEFERRED_DECISIONS`; decisión humana #3 (Identity & Organizations primero).

---

## Objetivo

Definir e **implementar** de extremo a extremo la **identidad existente + organizaciones B2B**: creación, ciclo de vida, membresías, invitaciones, roles/permisos org-scoped, contexto de organización activa, aislamiento por aplicación, auditoría y compatibilidad temporal para usuarios sin organización.

**Cierre:** `evidence/spec-closure.md`.

---

## Fuera de alcance (explícito)

CRM · prospectos · cotizaciones · contratos comerciales · planes · suscripciones · facturación · pagos · artistas empresariales · derechos · campañas · Customer Success completo · soporte · migración a PostgreSQL · segundo sistema de autenticación · SQL/migraciones ejecutadas · cambios a feature.json / Constitución / TRACEABILITY-MASTER.

---

## Principio de diseño

```text
negocio → OE/OT/OO → capacidades → procesos → actores → CU → reglas → estados
→ datos → backend → frontend → reportes → KPIs → pruebas → evidencia
```

Fuente: Constitución 2.0.0 P0; modelo 015.

---

## User Stories (documentales / futuras de implementación)

### US1 — Reutilizar identity (P1)

Como plataforma, necesito conservar login/registro/sesión bearer y roles técnicos, extendiendo sin reemplazar auth.

**Independent Test:** Login existente sigue funcionando; no hay segundo auth.

### US2 — Crear y gobernar organización (P1)

Como usuario autenticado, creo una org (`provisioning`→`active`) y soy `owner` inicial.

### US3 — Invitar y aceptar miembros (P1)

Como administrator/owner, invito por email; el invitado acepta con token de un solo uso.

### US4 — Roles y permisos org-scoped (P1)

Como owner/admin, asigno roles; el backend enforce permisos (deny by default).

### US5 — Contexto y aislamiento (P1)

Selecciono organización activa; no accedo a Org B desde Org A; platform access elevado auditado.

### US6 — Usuario sin organización (P2)

Conservo pantallas personales/demo; rutas empresariales exigen org context.

### US7 — Auditoría (P2)

Operaciones sensibles dejan `audit_log` sin secretos.

---

## Requirements (diseño)

- **FR-001** Reutilizar `app_user`, `app_session`, `app_email_code`, bearer auth.
- **FR-002** Entidad organization con estados provisioning/active/suspended_by_platform/closed.
- **FR-003** organization_member separado de user; multi-org; roles por org.
- **FR-004** organization_invitation con token hasheado, expiración, un solo uso.
- **FR-005** Catálogo roles org + matriz rol→permiso; roles plataforma separados.
- **FR-006** Contexto org activo validado en backend (no confiar en client alone).
- **FR-007** Aislamiento por `organization_id` en aplicación + pruebas (DuckDB no aísla nativo).
- **FR-008** audit_log para acciones sensibles listadas.
- **FR-009** Compatibilidad usuario sin org (decisión 015 #7).
- **FR-010** Contratos API `/api/v1` y flujos FE diseñados, no implementados en este borrador.
- **FR-011** Migración segura: sin orgs ficticias automáticas; seeds demo explícitos.
- **NFR-001** Naming honesto: DESIGN_APPROVED ≠ implementado.
- **NFR-002** No PAN/CVV; no billing en 016.
- **NFR-003** Frontend no sustituye autorización backend.

---

## Success Criteria (cierre del borrador 016)

1. Alcance vertical completo identity+orgs.  
2. Identity actual reutilizada (assessment).  
3. Org/member/invitation con estados.  
4. Roles/permisos definidos.  
5. Aislamiento diseñado.  
6. Compatibilidad sin org resuelta.  
7. Datos con propietario.  
8. APIs y UI especificadas.  
9. Migración diseñada.  
10. Pruebas de seguridad/cross-tenant diseñadas.  
11. Nada presentado como implementado sin serlo.

---

## Artefactos

Ver carpeta: assessment, domain models, api-contracts, frontend-flows, migration, test-strategy, traceability, plan, tasks, checklist.
