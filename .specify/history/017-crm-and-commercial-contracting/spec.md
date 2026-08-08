> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: CRM and Commercial Contracting

**Feature Branch**: `017-crm-and-commercial-contracting` *(propuesta; Git manual)*  
**Feature Directory**: `.specify/history/017-crm-and-commercial-contracting/`  
**Created**: 2026-07-11  
**Status**: **DESIGN_APPROVED** — **IMPLEMENTATION_COMPLETE** · **CLOSED_WITH_ACCEPTED_DEBT** (J6 2026-07-11)  
**Input**: Segunda capacidad de implementación tras 016 Identity & Organizations (mapa 015 orden 2).  
**Readiness:** CLOSED_WITH_ACCEPTED_DEBT. **J0–J6 COMPLETE**. Playwright E2E = NOT_VERIFIED (accepted debt).

**Número de spec:** **017**

**Prerrequisitos:** Constitución v2.0.0; spec 015 `CLOSED_WITH_DEFERRED_DECISIONS`; spec 016 `CLOSED_WITH_ACCEPTED_DEBT`.

**feature.json:** apunta a 017 (activado en J0).

---

## Objetivo

Implementar el **CRM interno sales-assisted de VOXMETRIKS** y el cierre comercial hasta **conversión a organización** (dominio 016), sin activar suscripción, factura ni pago.

```text
prospecto → contacto → oportunidad → actividades → cotización → negociación
→ aprobación → contrato comercial → aceptación → conversión a organización
→ handoff futuro a suscripciones
```

---

## Alcance (IN)

- CRM platform-scoped (pre-conversión sin `organization_id` propietario).
- Prospectos, contactos, oportunidades, pipeline, actividades.
- Cotizaciones versionadas, descuentos propuestos, aprobaciones.
- Contrato comercial y aceptación académica registrada (no e-sign legal afirmada).
- Conversión / vínculo a Organizations (016).
- Roles internos sales + permisos CRM.
- Trazabilidad, auditoría, APIs/UI/pruebas **diseñadas**.
- KPIs comerciales **propuestos** (sin resultados inventados).

---

## Fuera de alcance (OUT)

| Tema | Estado |
|------|--------|
| Catálogo definitivo de planes / `plan` publish | DEFERRED → spec futura subscriptions |
| Subscription / entitlements / trial | OUT |
| Invoice / payment / reconciliation | OUT |
| Billing profile fiscal | OUT |
| Self-service checkout | OUT (camino 015 alternativo) |
| Campañas musicales | OUT |
| Customer Success completo | OUT |
| Firma electrónica legal real / proveedor documentos | OUT |
| Rights contracts (catálogo) | OUT (distinto de commercial_contract) |
| Precios/umbrales definitivos | DEFERRED (configurables) |
| Envío real de email | OUT (solo referencias) |
| SQL / tablas / código | OUT en este borrador |

---

## Principio de diseño

```text
negocio → OE/OT/OO → capacidades → procesos → actores → CU → reglas → estados
→ datos → backend → frontend → reportes → KPIs → pruebas → evidencia
```

Fuente: Constitución 2.0.0 P0; golden path 015 A (sales-assisted).

---

## User Stories (documentales — futuras de implementación)

### US1 — Prospecto y contacto (P1)

Como `sales_agent`, registro un prospecto platform-scoped y sus contactos sin crear usuario de plataforma automáticamente.

### US2 — Oportunidad y pipeline (P1)

Como `sales_agent`, abro y avanzo una oportunidad con valor estimado, moneda única y razón de pérdida cuando aplique.

### US3 — Actividades (P2)

Como `sales_agent`, registro notas, llamadas, reuniones, tareas y follow-ups con auditoría (sin envío real de email).

### US4 — Cotización versionada (P1)

Como `sales_agent`, elaboro cotizaciones con versiones inmutables tras envío; una moneda; precios propuestos; sin crear subscription.

### US5 — Aprobaciones (P1)

Como `sales_manager`, apruebo o rechazo descuentos/términos sobre umbral; `sales_agent` no autoaprueba sobre umbral.

### US6 — Contrato comercial (P1)

Como `sales_agent`/`sales_manager`, creo y acepto un contrato comercial con evidencia académica (actor, fecha, evidencia), sin afirmar firma legal.

### US7 — Conversión a organización (P1)

Como orquestación CRM + Organizations, convierto de forma idempotente: crear o vincular org 016, owner definido, historial CRM conservado, evento `CustomerConverted`, sin billing.

### US8 — Auditoría y aislamiento (P1)

Como `auditor`/`platform_admin`, consulto auditoría CRM; usuarios org-cliente **no** operan CRM pre-conversión.

---

## Requirements (diseño)

- **FR-001** CRM pre-conversión platform-scoped (BR-CRM-01/02 de 015).
- **FR-002** Prospect con estados lead/new→converted (refinar: `lead` alias de `new` si se unifica).
- **FR-003** Contactos con roles conceptuales (decision_maker, authorized_signatory, primary); sin auto-user.
- **FR-004** Opportunity con estados ampliados vs 015: open, qualified, proposal, negotiation, won, lost, canceled.
- **FR-005** Actividades tipadas + auditoría.
- **FR-006** Quotation + version + items; inmutabilidad post-sent; no multi-currency; no subscription.
- **FR-007** Approval_request con separación de funciones.
- **FR-008** Commercial_contract distinto de subscription y de rights_contract.
- **FR-009** Conversión usa APIs/casos de Organizations 016; no orgs huérfanas; no doble conversión.
- **FR-010** Permisos CRM deny-by-default; backend enforce.
- **FR-011** APIs `/api/v1/crm/*` y `/api/v1/contracts/*` (o unificado bajo crm) diseñadas.
- **FR-012** Frontend CRM interno diseñado; sin billing UI.
- **FR-013** Auditoría sin secretos/tokens; PII comercial controlada.
- **NFR-001** DESIGN_APPROVED ≠ implementado.
- **NFR-002** No PAN/CVV; no cumplimiento legal afirmado.
- **NFR-003** Probabilidad de oportunidad = manual/regla configurable, **no** predicción IA.
- **NFR-004** DuckDB académico: aislamiento por aplicación (como 016).

---

## Success Criteria (cierre del borrador 017)

1. CRM platform-scoped antes de conversión.  
2. Procesos con máquinas de estado.  
3. Roles sales separados de roles org-cliente.  
4. Cotizaciones versionadas.  
5. Aprobaciones definidas.  
6. Contrato ≠ subscription.  
7. Conversión usa Organizations 016.  
8. Sin billing oculto.  
9. APIs/UI/pruebas trazadas.  
10. Nada futuro marcado como implementado.

---

## Artefactos

Ver carpeta: assessment, domain models, lifecycle, rules, roles, data-model, api-contracts, frontend-flows, audit-and-security, migration, test-strategy, traceability, plan, tasks, checklist.

---

## Relación con 015 / 016

| Fuente | Uso en 017 |
|--------|------------|
| 015 commercial/operational/golden path A | Proceso sales-assisted |
| 015 state machines 1–4 | Base; 017 **refina** opportunity/quotation/contract |
| 015 BR-COM / BR-CRM | Heredadas + ampliadas |
| 016 Organizations | Único dueño de create/link org + invite owner |
| 016 Identity | Auth bearer; usuarios sales = `app_user` con roles plataforma |

---

## Decisiones humanas pendientes

Ver sección final de `plan.md` y `checklist.md` (umbrales, naming `app_*`, unificación lead/new, owner de conversión, etc.).
