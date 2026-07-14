# Matriz Maestra de Trazabilidad — Capa Operativa Voxmetriks

**Versión:** 3.3.0 | **Ratificado documental:** 2026-06-20 | **Última actualización:** 2026-07-14  
**Alcance:** Specs operativas `001`–`011` + fundamento **015** + **016–029** (incluye **029** Personal Music Subscriptions)  
**Estado del sistema empresarial:** **ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT** (028)  
**Línea B2C personal:** Spec **029** — `CLOSED_WITH_ACCEPTED_DEBT`  
**Nota:** Numeración corregida — **024 ≠ Royalties**, **025 ≠ Payouts**. Royalties/Payouts quedan **OUT_OF_SCOPE** (specs futuras no numeradas).  
**Cadena:** OE → OT → OO → Meta → Departamento → Paquete → CU → HU → FR → CA → Impl → Evidencia  
**Constitución vigente:** 2.0.0 (`.specify/memory/constitution.md`)

Referencia: Constitución §12. Documento canónico transversal; las specs individuales incluyen subconjunto y detalle de casos de uso / historias de usuario.

### Personal Music Subscriptions — Spec 029 (cierre 2026-07-14)

| Campo | Valor |
|-------|-------|
| Spec | `029-personal-music-subscriptions` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Alcance | B2C Free/Individual/Duo/Familiar separado de B2B Spec 018 |
| Código | `packages/personal_subscriptions` BE · `packages/personal-account` FE |
| API | `/api/v1/personal/*` |
| Gates | pytest S029 · pytest full 799 · S028 golden · FE lint/unit/build |
| feature.json | apunta a **029** |
| Demo | `docs/DEMO-ACCOUNTS.md` · `seed_integrated_demo.py` · cleanup test orgs |
| Cierre integrado | B2C + B2B listo para demostración local (2026-07-14) |

Debt: Playwright NOT_VERIFIED; MOCK pay/email; queue avanzado soft-flag; renewals on-read.

### Enterprise Integration and Final Validation — Spec 028 (reopen 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `028-enterprise-integration-and-final-validation` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado del sistema | **ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT** |
| Alcance | Integración 024/025 + golden path ampliado + trazabilidad corregida · **integración documental B2C+B2B vía Spec 029** |
| Gates | golden-path pytest PASS · reporting R* · CS S* · FE lint/unit/build |
| Código | `test_enterprise_golden_path_s028.py` · packages `reporting`, `customer_success` |
| Evidencia | `automation/specs/028-enterprise-integration-and-final-validation/` |
| feature.json | historial 028; activo **029** mientras se cierra personal |

Debt: Playwright/Docker NOT_VERIFIED; MOCK email/payment; no GDPR cert; DuckDB academic; royalties/payouts OUT_OF_SCOPE.

### Executive Reporting and Business Decisions — Spec 024 (cierre 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `024-executive-reporting-and-business-decisions` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Código | `packages/reporting` BE · `packages/reporting` FE |
| API | `/api/v1/reports`, `/api/v1/business-decisions` |

### Customer Success and Support — Spec 025 (cierre 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `025-customer-success-and-support` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Código | `packages/customer_success` BE · `packages/customer-success` FE |
| API | `/api/v1/customer-success`, `/api/v1/support` |

### Platform Operations and Integrations — Spec 027 (cierre 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `027-platform-operations-and-integrations` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest R1–R3, R5 PASS · FE unit L4 PASS |
| Código | `packages/platform_ops` BE · `packages/platform-ops` FE |
| API | `/api/v1/platform-ops` |
| Integración | Reuses `platform/jobs`, `billing.PaymentProvider`; MOCK console email/notification |
| Evidencia | `automation/specs/027-platform-operations-and-integrations/evidence/` |

Debt aceptada: Playwright NOT_VERIFIED; conceptual backup; MOCK adapters only; no production HA claims.

### Compliance, Privacy and Global Audit — Spec 026 (cierre 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `026-compliance-privacy-and-global-audit` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest Q1–Q3, Q5 PASS · FE unit L4 PASS |
| Código | `packages/compliance` BE · `packages/compliance` FE |
| API | `/api/v1/compliance` |
| Permisos | `compliance.*`, `privacy.*`, `incident.manage`, `audit.search` (org + platform) |
| Evidencia | `automation/specs/026-compliance-privacy-and-global-audit/evidence/` |

Debt aceptada: Playwright NOT_VERIFIED; no automated warehouse purge; 024/025 absent.

### Engagement and Business Analytics — Spec 023 (cierre 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `023-engagement-and-business-analytics` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest P1–P3, P5 PASS · FE unit L4 PASS |
| Código | `packages/business_analytics` BE · `packages/business-analytics` FE |
| API | `/api/v1/business-analytics` |
| Integración | Reuses `fact_streaming`, `agg_daily_streams`; links `campaign_roi` from Spec 022 |
| Evidencia | `automation/specs/023-engagement-and-business-analytics/evidence/` |

Debt aceptada: trends/comparatives stubs; no AI recommendations; Playwright NOT_VERIFIED.

### Campaigns, Budgets and ROI — Spec 022 (cierre 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `022-campaigns-budgets-and-roi` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest O1–O3, O5 PASS (44 tests) · FE unit L4 PASS |
| Código | `packages/campaigns` BE · `packages/campaigns` FE |
| API | `/api/v1/campaigns` |
| Permisos | `campaign.view/create/update/approve/expense/close` seeded |
| ROI | Honest unavailable state when prerequisites missing; streams ≠ money |
| Evidencia | `automation/specs/022-campaigns-budgets-and-roi/evidence/` |

Debt aceptada: Playwright NOT_VERIFIED; no FX conversion.

### Catalog Rights and Contracts — Spec 021 (cierre 2026-07-12)

| Campo | Valor |
|-------|-------|
| Spec | `021-catalog-rights-and-contracts` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de diseño | **DESIGN_APPROVED** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest **98 PASS** (catalog_rights) · schema N1 32 · use_cases N2 36 · api N3 19 · security N5 11 · FE unit L4 PASS |
| E2E Playwright | **NOT_VERIFIED** (no browser framework; accepted debt) |
| Código | `packages/catalog_rights` BE · `packages/catalog-rights` FE · `organizations/catalogs` (rights perms) |
| Integración 020 | `app_artist_profile` linkage for assets/parties |
| Evidencia | `automation/specs/021-catalog-rights-and-contracts/evidence/` |
| feature.json | apunta a **021** |

Debt aceptada:
- Playwright / E2E browser tests no implementados
- `valid_to` no auto-transiciona a `expired`
- `warehouse_album_id` sin validación (no existe `dim_album`)
- Coverage/aprobaciones como secciones en páginas de detalle (no rutas top-level)

Relación 015→016→017→018→019→020→021:

```text
015 DESIGN_APPROVED (fundamento)
  → 016 CLOSED_WITH_ACCEPTED_DEBT (Identity & Organizations)
  → 017 CLOSED_WITH_ACCEPTED_DEBT (CRM & commercial contracting)
  → 018 CLOSED_WITH_ACCEPTED_DEBT (Plans & Subscriptions)
  → 019 CLOSED_WITH_ACCEPTED_DEBT (Billing, Payments & Reconciliation)
  → 020 CLOSED_WITH_ACCEPTED_DEBT (Artists & Team Management)
  → 021 CLOSED_WITH_ACCEPTED_DEBT (Catalog Rights & Contracts)
  → 022 CLOSED_WITH_ACCEPTED_DEBT (Campaigns, Budgets & ROI)
  → 023 CLOSED_WITH_ACCEPTED_DEBT (Engagement & Business Analytics)
  → 024/025 NOT_PRESENT_IN_WORKSPACE (Royalties/Payouts)
  → 026 CLOSED_WITH_ACCEPTED_DEBT (Compliance, Privacy & Global Audit)
  → 027 CLOSED_WITH_ACCEPTED_DEBT (Platform Operations & Integrations)
  → 028 CLOSED_WITH_ACCEPTED_DEBT (Integration & Final Validation)
  → ENTERPRISE_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT
  → futuras (029+) según roadmap 015 — CS/Support/Exec report diferidos; 024/025 ausentes
```

### Artists and Team Management — Spec 020 (cierre 2026-07-11)

| Campo | Valor |
|-------|-------|
| Spec | `020-artists-and-team-management` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de diseño | **DESIGN_APPROVED** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest **70 PASS** (artists) · schema M1 · use_cases M2 · api M3 · security M5 · FE unit L4 PASS |
| E2E Playwright | **NOT_VERIFIED** (accepted debt) |
| Código | `packages/artists` BE · `packages/artists` FE · `organizations/catalogs` (artist perms) |
| API | Business profiles at **`/api/v1/artists`**; analytics catalog at **`/api/v1/catalog/artists`** |
| Evidencia | `automation/specs/020-artists-and-team-management/evidence/` |

Debt aceptada:
- Playwright E2E NOT_VERIFIED
- Frontend UI routes remain `/artist-profiles` (distinct from streaming `/artists`)
- No SQL compound UNIQUE; DELETE+INSERT for profile mutations (DuckDB)
- No UnlinkWarehouseArtist endpoint

### Billing, Payments and Reconciliation — Spec 019 (cierre 2026-07-11)

| Campo | Valor |
|-------|-------|
| Spec | `019-billing-payments-and-reconciliation` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de diseño | **DESIGN_APPROVED** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest **451 PASS** (61 billing) · schema L1 25 · use_cases L2 18 · api L3 11 · security L5 7 · FE unit L4 PASS |
| E2E Playwright | **NOT_VERIFIED** (no browser framework; accepted debt) |
| Código | `packages/billing` BE · `packages/billing` FE · `organizations/catalogs` (billing perms) |
| Integración 018 | `notify_subscription_past_due` / `notify_subscription_recovered` via orchestration |
| Evidencia | `automation/specs/019-billing-payments-and-reconciliation/evidence/` |
| feature.json | apunta a **019** |

Debt aceptada:
- Playwright / E2E browser tests no implementados (sin framework de browser configurado)
- `platform_finance` break-glass role: deferred
- `platform_admin` billing access: deferred

Relación 015→016→017→018→019:

```text
015 DESIGN_APPROVED (fundamento)
  → 016 CLOSED_WITH_ACCEPTED_DEBT (Identity & Organizations)
  → 017 CLOSED_WITH_ACCEPTED_DEBT (CRM & commercial contracting)
  → 018 CLOSED_WITH_ACCEPTED_DEBT (Plans & Subscriptions)
  → 019 CLOSED_WITH_ACCEPTED_DEBT (Billing, Payments & Reconciliation)
  → futuras (artists empresariales, campaigns, …) aún IMPLEMENTATION_PENDING
```

### Plans and Subscriptions — Spec 018 (cierre 2026-07-11)

| Campo | Valor |
|-------|-------|
| Spec | `018-plans-and-subscriptions` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de diseño | **DESIGN_APPROVED** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest 390+ PASS · schema K1 23 · use_cases K2 28 · api K3 15 · security K5 20 |
| E2E Playwright | **NOT_VERIFIED** (no browser framework; accepted debt) |
| Código | `packages/subscriptions` BE · `packages/subscriptions` FE · `organizations/catalogs` (subscription perms) |
| Evidencia | `automation/specs/018-plans-and-subscriptions/evidence/` |
| feature.json | avanzado a **019** en J0 de Spec 019 |

### CRM and Commercial Contracting — Spec 017 (cierre 2026-07-11)

| Campo | Valor |
|-------|-------|
| Spec | `017-crm-and-commercial-contracting` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de diseño | **DESIGN_APPROVED** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest **304 PASS** · FE lint 0 err / unit **111** / build PASS · warehouse validate PASS · security J5 PASS |
| E2E Playwright | **NOT_VERIFIED** (0 CRM specs; accepted debt) |
| Código | `packages/platform_rbac` · `packages/crm` · `packages/contracts` · FE `packages/crm` |
| Evidencia | `automation/specs/017-crm-and-commercial-contracting/evidence/spec-closure.md` |
| feature.json | apunta a **017** |

**MUST NOT** afirmar subscriptions/billing/pagos/campañas como implementados. 017 entrega CRM + commercial contract + conversión a Organizations.

Relación 015→016→017:

```text
015 DESIGN_APPROVED (fundamento)
  → 016 CLOSED_WITH_ACCEPTED_DEBT (Identity & Organizations)
  → 017 CLOSED_WITH_ACCEPTED_DEBT (CRM & commercial contracting)
  → futuras (plans/subscriptions, billing, …) aún IMPLEMENTATION_PENDING
```

### Identity & Organizations — Spec 016 (cierre 2026-07-11)

| Campo | Valor |
|-------|-------|
| Spec | `016-identity-and-organizations` |
| Cierre | **CLOSED_WITH_ACCEPTED_DEBT** |
| Estado de diseño | **DESIGN_APPROVED** |
| Estado de implementación | **IMPLEMENTATION_COMPLETE** |
| Gates | pytest 231 PASS · FE lint/unit/build PASS · warehouse validate PASS · security I5 PASS |
| E2E Playwright | **NOT_VERIFIED** (0 specs; accepted debt) |
| Código | `apps/backend/app/packages/organizations/` · `apps/frontend/src/app/packages/organizations/` · identity reutilizado |
| Evidencia | `automation/specs/016-identity-and-organizations/evidence/spec-closure.md` |
| feature.json | permanece en 016 al cierre I6; **activado a 017 en J0** |

**MUST NOT** afirmar CRM/billing/campañas/artistas empresariales como implementados **en 016**. 016 entrega solo identity+organizations. CRM = **017**.

Relación 015→016:

```text
015 DESIGN_APPROVED (fundamento)
  → 016 CLOSED_WITH_ACCEPTED_DEBT (primera capacidad implementada)
  → 017 CLOSED_WITH_ACCEPTED_DEBT (CRM & contracts)
  → futuras specs (subscriptions, billing, …) aún IMPLEMENTATION_PENDING
```

### Fundamento empresarial — Spec 015 (2026-07-11)

| Campo | Valor |
|-------|-------|
| Spec | `015-enterprise-business-foundation` |
| Cierre | `CLOSED_WITH_DEFERRED_DECISIONS` |
| Producto | B2B SaaS de gestión e inteligencia musical |
| Pagador | Organización musical |
| Estado de diseño | **DESIGN_APPROVED** |
| Estado de implementación | **IMPLEMENTATION_PENDING** |
| Primera implementación aprobada | **016 Identity & Organizations** — **CLOSED_WITH_ACCEPTED_DEBT** |

**MUST NOT** enlazar la 015 a tablas DuckDB, endpoints o pantallas empresariales que **aún no existen**. La matriz de filas 001–011 describe la capa operativa técnica existente; la 015 es el **modelo de negocio** sobre el que se construirán specs futuras.

#### Relaciones de trazabilidad 015 (diseño)

```text
Producto B2B (015)
  → Objetivos estratégicos (strategic-model.md)
    → Objetivos tácticos (tactical-model.md)
      → Objetivos / procesos operativos (operational-model.md)
        → Capacidades (capability-map.md)
          → Dominios (domain-boundaries.md) — DESIGN_APPROVED
            → Golden Path (business-golden-path.md)
              → Futuras specs (future-specification-map.md) — IMPLEMENTATION_PENDING
```

| Dominio empresarial (015) | Estado |
|---------------------------|--------|
| organizations | **IMPLEMENTED** (016 CLOSED_WITH_ACCEPTED_DEBT) |
| crm, contracts (commercial) | **IMPLEMENTED** (017 CLOSED_WITH_ACCEPTED_DEBT) |
| subscriptions | **IMPLEMENTED** (018 CLOSED_WITH_ACCEPTED_DEBT) |
| billing, payments, reconciliation | **IMPLEMENTED** (019 CLOSED_WITH_ACCEPTED_DEBT) |
| artists empresariales, catalog_rights, campaigns | DESIGN_APPROVED / IMPLEMENTATION_PENDING |
| reporting empresarial, customer_success, support, compliance | DESIGN_APPROVED / IMPLEMENTATION_PENDING |

| Dominio técnico (código actual) | Relación con 015 |
|---------------------------------|------------------|
| identity/users, catalog/streaming, engagement, analytics, ai, platform | Base técnica; no sustituyen dominios empresariales |

Evidencia de cierre 015: `automation/specs/015-enterprise-business-foundation/evidence/spec-closure.md`.

### Deuda de rutas (Spec 014 G — 2026-07-11)

Las columnas **Evidencia** de esta matriz aún citan rutas históricas (`backend/...`, `frontend/...`, `packages/users`, `packages/streaming`) anteriores al monorepo `apps/` y a la consolidación D2 (`identity` / `catalog` / `engagement`).

**Mapeo canónico actual (no reescribe filas históricas):**

| Histórico en matriz | Canónico / adaptador |
|---------------------|----------------------|
| `backend/app/...` | `apps/backend/app/...` |
| `frontend/src/...` | `apps/frontend/src/...` |
| `packages/users` | `packages/identity` (+ shim `packages/users`) |
| `packages/streaming` (catálogo/engagement) | `packages/catalog` + `packages/engagement` (+ shim `streaming`; audio permanece en streaming) |
| `elt/pipelines/...` | `analytics/elt/pipelines/...` |

Actualización fila-a-fila de las 248 evidencias = **deuda aceptada** (spec posterior / herramienta de regeneración). No se reescriben filas aquí para no fingir historial.

**Cierre Spec 014:** `CLOSED_WITH_ACCEPTED_DEBT` — `automation/specs/014-repository-stabilization-domain-foundation/evidence/spec-closure.md`.

**Cierre Spec 015:** `CLOSED_WITH_DEFERRED_DECISIONS` — fundamento empresarial **DESIGN_APPROVED**; CRM/billing/etc. siguen **IMPLEMENTATION_PENDING**.

**Cierre Spec 016:** `CLOSED_WITH_ACCEPTED_DEBT` — Identity & Organizations **IMPLEMENTATION_COMPLETE**; Playwright E2E NOT_VERIFIED; ver `accepted-debt.md`.

**Cierre Spec 018:** `CLOSED_WITH_ACCEPTED_DEBT` — Plans & Subscriptions **IMPLEMENTATION_COMPLETE**; pytest K1+K2+K3+K5 PASS; Playwright NOT_VERIFIED.

**Cierre Spec 019:** `CLOSED_WITH_ACCEPTED_DEBT` — Billing, Payments & Reconciliation **IMPLEMENTATION_COMPLETE**; pytest 451 PASS (61 billing); Playwright NOT_VERIFIED; platform_finance/admin deferred.

### Leyenda Impl

| Valor | Significado |
|-------|-------------|
| **Implementado** | Comportamiento verificable en código según FR |
| **Parcial** | Implementado con brechas documentadas en spec/auditoría |
| **No implementado** | FR no presente en código |

### Resumen implementación

| Métrica | Valor |
|---------|------:|
| Filas totales | 248 |
| Implementado | 240 |
| Parcial | 8 |
| No implementado | 0 |
| Pendiente (sin evidencia) | 0 |

Evidencia auditada: `specs/_tools/implementation_evidence.py` + `SPEC-008-011-EVIDENCE-AUDIT.md`.

| Spec | OE | OT | OO | Meta | Dept | Paquete | CU | HU | FR | CA | Impl | Evidencia |
|------|----|----|-----|------|------|---------|----|----|----|----|------|-----------|
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-01 | US-01 | FR-001 | CA-001 | Implementado | `backend/app/packages/users/routes/users.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-01 | US-01 | FR-002 | CA-001 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-01 | US-01 | FR-003 | CA-001 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-01 | US-01 | FR-004 | CA-008 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-01 | US-01 | FR-017 | CA-001 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-01 | US-01 | FR-018 | CA-001 | Implementado | `frontend/src/app/core/services/auth.service.ts` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-02 | US-02 | FR-005 | CA-002 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-02 | US-02 | FR-006 | CA-002 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-02 | US-02 | FR-007 | CA-002 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-02 | US-02 | FR-020 | CA-002 | Implementado | `frontend/src/app/core/i18n/translations.ts` |
| 001 | OE-01 | OT-01 | OO-01 | M-01 | DEP-01 | PKG-01 | CU-03 | US-03 | FR-008 | CA-003 | Implementado | `backend/app/packages/users/routes/users.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-01 | DEP-01 | PKG-01 | CU-03 | US-03 | FR-009 | CA-003 | Implementado | `backend/app/packages/users/services/auth_deps.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-04 | US-04 | FR-010 | CA-004 | Implementado | `backend/app/packages/users/routes/users.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-04 | US-04 | FR-011 | CA-004 | Implementado | `backend/app/packages/users/services/user_service.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-05 | US-05 | FR-012 | CA-005 | Implementado | `frontend/src/app/core/services/auth.service.ts` |
| 001 | OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-06 | US-06 | FR-013 | CA-006 | Implementado | `frontend/src/app/core/guards/auth.guard.ts` |
| 001 | OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-06 | US-06 | FR-014 | CA-006 | Parcial | `frontend/src/app/app.routes.ts` |
| 001 | OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-06 | US-07 | FR-015 | CA-007 | Implementado | `frontend/src/app/core/guards/engineer.guard.ts` |
| 001 | OE-01 | OT-01 | OO-01 | M-01 | DEP-01 | PKG-01 | CU-07 | US-01 | FR-016 | CA-001 | Implementado | `backend/app/packages/users/services/user_storage.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-01 | DEP-01 | PKG-01 | CU-07 | US-02 | FR-016 | CA-002 | Implementado | `backend/app/packages/users/services/user_storage.py` |
| 001 | OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-07 | US-02 | FR-019 | CA-002 | Implementado | `frontend/src/app/core/interceptors/api.interceptor.ts` |
| 001 | OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-07 | US-06 | FR-019 | CA-006 | Implementado | `frontend/src/app/core/interceptors/api.interceptor.ts` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P01 | US-P01 | FR-P01 | CA-001 | Implementado | `backend/app/packages/streaming/routes/playlists.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P02 | US-P01 | FR-P02 | CA-001 | Implementado | `backend/app/packages/streaming/routes/playlists.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P03 | US-P01 | FR-P03 | CA-001 | Implementado | `backend/app/packages/streaming/services/playlist_service.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P04 | US-P01 | FR-P04 | CA-001 | Implementado | `backend/app/packages/streaming/routes/playlists.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P05 | US-P01 | FR-P05 | CA-001 | Implementado | `backend/app/packages/streaming/routes/playlists.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P06 | US-P02 | FR-P06 | CA-002 | Implementado | `backend/app/packages/streaming/routes/playlists.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P07 | US-P02 | FR-P07 | CA-002 | Implementado | `backend/app/packages/streaming/routes/playlists.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P01 | US-P01 | FR-P08 | CA-006 | Implementado | `backend/app/packages/users/services/auth_deps.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P02 | US-P01 | FR-P09 | CA-004 | Implementado | `frontend/src/app/packages/streaming/playlists/playlists.component.ts` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P04 | US-P01 | FR-P10 | CA-004 | Implementado | `frontend/src/app/packages/streaming/playlists/playlists.component.ts` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P06 | US-P02 | FR-P11 | CA-005 | Implementado | `frontend/src/app/shared/components/add-to-playlist-btn/add-to-playlist-btn.component.ts` |
| 002 | OE-01 | OT-02 | OO-02 | M-1A | DEP-02 | PKG-02 | CU-P03 | US-P01 | FR-P12 | CA-001 | Implementado | `backend/app/packages/streaming/services/playlist_service.py` |
| 002 | OE-01 | OT-02 | OO-02 | M-1D | DEP-02 | PKG-02 | CU-P07 | US-P03 | FR-P13 | CA-002 | Implementado | `frontend/src/app/packages/streaming/playlists/playlists.component.ts` |
| 002 | OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F01 | US-F01 | FR-F01 | CA-003 | Implementado | `backend/app/packages/streaming/routes/favorites.py` |
| 002 | OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F02 | US-F01 | FR-F02 | CA-003 | Implementado | `backend/app/packages/streaming/services/favorite_service.py` |
| 002 | OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F03 | US-F01 | FR-F03 | CA-003 | Implementado | `backend/app/packages/streaming/services/favorite_service.py` |
| 002 | OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F04 | US-F01 | FR-F04 | CA-005 | Implementado | `frontend/src/app/packages/streaming/liked/liked.component.ts` |
| 002 | OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F04 | US-F01 | FR-F05 | CA-005 | Implementado | `frontend/src/app/shared/components/favorite-btn/favorite-btn.component.ts` |
| 002 | OE-01 | OT-02 | OO-03 | M-1B | DEP-02 | PKG-02 | CU-F01 | US-F01 | FR-F06 | CA-003 | Implementado | `frontend/src/app/packages/streaming/services/favorites.service.ts` |
| 002 | OE-01 | OT-02 | OO-03 | M-1C | DEP-02 | PKG-02 | CU-F01 | US-F01 | FR-F01 | CA-003 | Implementado | `backend/app/packages/streaming/routes/favorites.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C01 | US-C01 | FR-C01 | CA-001 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C02 | US-C01 | FR-C02 | CA-001 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C03 | US-C01 | FR-C03 | CA-001 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C03 | US-C01 | FR-C04 | CA-001 | Implementado | `backend/app/packages/streaming/routes/genres.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C04 | US-C02 | FR-C07 | CA-001 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4C | DEP-02 | PKG-02 | CU-C05 | US-C02 | FR-C08 | CA-001 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4C | DEP-02 | PKG-02 | CU-C05 | US-C02 | FR-C09 | CA-001 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4C | DEP-02 | PKG-02 | CU-C05 | US-C02 | FR-C10 | CA-003 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C06 | US-C01 | FR-C05 | CA-001 | Implementado | `backend/app/packages/streaming/routes/genres.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C06 | US-C01 | FR-C06 | CA-001 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C04 | US-C02 | FR-C11 | CA-001 | Implementado | `frontend/src/app/app.routes.ts` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C01 | US-C01 | FR-C12 | CA-004 | Parcial | `frontend/src/app/packages/streaming/artists/artists.component.html` |
| 003 | OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S01 | US-S01 | FR-S01 | CA-002 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S02 | US-S01 | FR-S02 | CA-002 | Implementado | `frontend/src/app/packages/streaming/search/search.component.ts` |
| 003 | OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S01 | US-S01 | FR-S03 | CA-002 | Parcial | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S02 | US-S01 | FR-S04 | CA-002 | Implementado | `frontend/src/app/packages/streaming/search/search.component.html` |
| 003 | OE-01 | OT-03 | OO-05 | M-4B | DEP-02 | PKG-02 | CU-S03 | US-S01 | FR-S01 | CA-002 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-15 | M-4C | DEP-02 | PKG-02 | CU-AF01 | US-AF01 | FR-AF01 | CA-003 | Implementado | `frontend/src/app/packages/streaming/audio-features/audio-features.component.ts` |
| 003 | OE-01 | OT-03 | OO-15 | M-4C | DEP-02 | PKG-02 | CU-AF01 | US-AF01 | FR-AF02 | CA-003 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 003 | OE-01 | OT-03 | OO-15 | M-4C | DEP-02 | PKG-02 | CU-AF02 | US-C02 | FR-C10 | CA-003 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 003 | OE-01 | OT-03 | OO-15 | M-4C | DEP-02 | PKG-02 | CU-AF01 | US-AF01 | FR-AF03 | CA-003 | Implementado | `frontend/src/app/packages/streaming/audio-features/audio-features.component.ts` |
| 003 | OE-01 | OT-03 | OO-04 | M-4A | DEP-02 | PKG-02 | CU-C05 | US-C03 | FR-C13 | CA-005 | Parcial | `frontend/src/app/shared/components/track-row/track-row.component.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R01 | FR-R01 | CA-001 | Implementado | `frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R01 | FR-R02 | CA-001 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R01 | FR-R03 | CA-005 | Implementado | `frontend/src/app/shared/config/demo-audio.config.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R01 | FR-R07 | CA-003 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6B | DEP-02 | PKG-03 | CU-R01 | US-R01 | FR-R03 | CA-001 | Implementado | `frontend/src/app/shared/config/demo-audio.config.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R02 | US-R01 | FR-R02 | CA-001 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R03 | US-R01 | FR-R04 | CA-001 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R04 | US-R01 | FR-R09 | CA-001 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R05 | US-R02 | FR-R05 | CA-002 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R06 | US-R02 | FR-R06 | CA-002 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R07 | US-R02 | FR-R10 | CA-002 | Implementado | `frontend/src/app/packages/streaming/playlists/playlists.component.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R02 | FR-R08 | CA-003 | Implementado | `frontend/src/app/shared/components/player-bar/player-bar.component.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R08 | US-R03 | FR-R12 | CA-001 | Implementado | `frontend/src/app/shared/components/now-playing-view/now-playing-view.component.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R04 | FR-R11 | CA-003 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-06 | M-6A | DEP-02 | PKG-03 | CU-R01 | US-R04 | FR-R13 | CA-006 | Implementado | `frontend/src/app/shared/services/music-player.service.ts` |
| 004 | OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H01 | US-H01 | FR-H01 | CA-004 | Implementado | `frontend/src/app/app.routes.ts` |
| 004 | OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H01 | US-H01 | FR-H02 | CA-004 | Implementado | `frontend/src/app/core/services/i18n.service.ts` |
| 004 | OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H02 | US-H01 | FR-H03 | CA-004 | Implementado | `frontend/src/app/packages/streaming/home/home.component.ts` |
| 004 | OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H03 | US-H01 | FR-H04 | CA-004 | Implementado | `frontend/src/app/packages/streaming/home/home.component.ts` |
| 004 | OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H04 | US-H01 | FR-H04 | CA-006 | Implementado | `frontend/src/app/packages/streaming/home/home.component.ts` |
| 004 | OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H03 | US-H01 | FR-H05 | CA-004 | Implementado | `frontend/src/app/packages/streaming/home/home.component.ts` |
| 004 | OE-01 | OT-04 | OO-07 | M-7A | DEP-02 | PKG-03 | CU-H02 | US-H01 | FR-H06 | CA-004 | Implementado | `frontend/src/app/packages/streaming/home/home.component.ts` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC01 | US-RC01 | FR-RC01 | CA-001 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC01 | US-RC01 | FR-RC03 | CA-001 | Implementado | `frontend/src/app/app.routes.ts` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC01 | US-RC01 | FR-RC04 | CA-001 | Implementado | `frontend/src/app/packages/recommendations/recommendations.component.ts` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC01 | US-RC01 | FR-RC06 | CA-001 | Implementado | `frontend/src/app/packages/recommendations/recommendations.component.html` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC01 | US-RC01 | FR-RC08 | CA-001 | Implementado | `backend/app/packages/analytics/services/analytics_service.py` |
| 005 | OE-01 | OT-05 | OO-08 | M-8B | DEP-03 | PKG-04 | CU-RC02 | US-RC01 | FR-RC02 | CA-001 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC02 | US-RC01 | FR-RC05 | CA-002 | Implementado | `frontend/src/app/packages/recommendations/recommendations.component.html` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC03 | US-RC02 | FR-RC07 | CA-006 | Implementado | `frontend/src/app/packages/recommendations/recommendations.component.ts` |
| 005 | OE-01 | OT-05 | OO-08 | M-8A | DEP-03 | PKG-04 | CU-RC04 | US-RC02 | FR-RC07 | CA-007 | Implementado | `frontend/src/app/packages/recommendations/recommendations.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI01 | US-HI01 | FR-HI01 | CA-003 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI01 | US-HI01 | FR-HI02 | CA-004 | Implementado | `frontend/src/app/packages/streaming/services/history.service.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI01 | US-HI01 | FR-HI03 | CA-003 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI01 | US-HI01 | FR-HI03 | CA-004 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI04 | US-HI02 | FR-HI01 | CA-003 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI04 | US-HI02 | FR-HI07 | CA-003 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI02 | US-HI02 | FR-HI04 | CA-005 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 005 | OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI02 | US-HI02 | FR-HI05 | CA-005 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI03 | US-HI02 | FR-HI06 | CA-003 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI03 | US-HI02 | FR-HI06 | CA-005 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI02 | US-HI02 | FR-HI08 | CA-005 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9A | DEP-03 | PKG-04 | CU-HI01 | US-HI03 | FR-HI09 | CA-006 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 005 | OE-01 | OT-05 | OO-09 | M-9B | DEP-03 | PKG-04 | CU-HI05 | US-HI04 | FR-HI10 | CA-003 | Implementado | `frontend/src/app/packages/history/history.component.ts` |
| 006 | OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF01 | US-PF01 | FR-PF01 | CA-001 | Implementado | `frontend/src/app/app.routes.ts` |
| 006 | OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF01 | US-PF01 | FR-PF02 | CA-001 | Implementado | `frontend/src/app/packages/users/users.component.ts` |
| 006 | OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF01 | US-PF01 | FR-PF03 | CA-001 | Implementado | `frontend/src/app/packages/users/users.component.ts` |
| 006 | OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF02 | US-PF01 | FR-PF04 | CA-002 | Implementado | `frontend/src/app/packages/users/users.component.html` |
| 006 | OE-01 | OT-06 | OO-11 | M-11A | DEP-01 | PKG-05 | CU-PF03 | US-PF02 | FR-PF05 | CA-001 | Implementado | `frontend/src/app/packages/users/users.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST01 | US-ST01 | FR-ST01 | CA-003 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST01 | US-ST01 | FR-ST02 | CA-003 | Implementado | `frontend/src/app/core/services/ui-preferences.service.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST02 | US-ST01 | FR-ST03 | CA-003 | Implementado | `frontend/src/app/core/services/i18n.service.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST01 | US-ST01 | FR-ST04 | CA-003 | Implementado | `frontend/src/app/core/services/ui-preferences.service.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST03 | US-ST02 | FR-ST05 | CA-004 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST03 | US-ST02 | FR-ST06 | CA-004 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST03 | US-ST02 | FR-ST08 | CA-004 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST04 | US-ST03 | FR-ST07 | CA-003 | Implementado | `frontend/src/app/core/services/ui-preferences.service.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10B | DEP-01 | PKG-05 | CU-ST04 | US-ST03 | FR-ST04 | CA-003 | Implementado | `frontend/src/app/core/services/ui-preferences.service.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST05 | US-ST04 | FR-ST09 | CA-005 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST05 | US-ST04 | FR-ST10 | CA-005 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST06 | US-ST05 | FR-ST11 | CA-006 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 006 | OE-01 | OT-06 | OO-10 | M-10A | DEP-01 | PKG-05 | CU-ST01 | US-ST01 | FR-ST12 | CA-007 | Implementado | `frontend/src/app/app.routes.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN01 | US-AN01 | FR-AN01 | CA-001 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN01 | US-AN01 | FR-AN08 | CA-001 | Implementado | `frontend/src/app/app.routes.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN01 | US-AN01 | FR-AN09 | CA-001 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN01 | US-AN01 | FR-AN24 | CA-001 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN01 | US-AN01 | FR-AN23 | CA-001 | Implementado | `frontend/src/app/pages/login/login.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN01 | US-AN01 | FR-AN26 | CA-011 | Parcial | `frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN02 | US-AN01 | FR-AN02 | CA-002 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN02 | US-AN01 | FR-AN10 | CA-002 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN07 | US-AN02 | FR-AN03 | CA-001 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12A | DEP-04 | PKG-06 | CU-AN07 | US-AN02 | FR-AN11 | CA-001 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12B | DEP-04 | PKG-06 | CU-AN03 | US-AN02 | FR-AN05 | CA-003 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12B | DEP-04 | PKG-06 | CU-AN03 | US-AN02 | FR-AN12 | CA-003 | Implementado | `frontend/src/app/app.routes.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12B | DEP-04 | PKG-06 | CU-AN03 | US-AN02 | FR-AN13 | CA-003 | Implementado | `frontend/src/app/packages/analytics/trending/trending.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12B | DEP-04 | PKG-06 | CU-AN03 | US-AN02 | FR-AN17 | CA-006 | Implementado | `frontend/src/app/packages/analytics/trending/trending.component.html` |
| 007 | OE-01 | OT-07 | OO-12 | M-12B | DEP-04 | PKG-06 | CU-AN03 | US-AN02 | FR-AN18 | CA-007 | Implementado | `frontend/src/app/packages/analytics/trending/trending.component.html` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN04 | US-AN03 | FR-AN07 | CA-004 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN04 | US-AN03 | FR-AN14 | CA-004 | Implementado | `frontend/src/app/app.routes.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN04 | US-AN03 | FR-AN04 | CA-004 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN04 | US-AN03 | FR-AN16 | CA-004 | Implementado | `frontend/src/app/packages/analytics/analytics/analytics.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN06 | US-AN03 | FR-AN06 | CA-004 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN06 | US-AN03 | FR-AN20 | CA-009 | Implementado | `frontend/src/app/packages/users/users.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN05 | US-AN04 | FR-AN15 | CA-005 | Implementado | `frontend/src/app/app.routes.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN05 | US-AN04 | FR-AN16 | CA-005 | Implementado | `frontend/src/app/packages/analytics/analytics/analytics.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN08 | US-AN05 | FR-AN01 | CA-008 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN08 | US-AN05 | FR-AN02 | CA-008 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN08 | US-AN05 | FR-AN19 | CA-008 | Implementado | `frontend/src/app/packages/streaming/home/home.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN09 | US-AN05 | FR-AN06 | CA-009 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN09 | US-AN05 | FR-AN05 | CA-009 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN09 | US-AN05 | FR-AN20 | CA-009 | Implementado | `frontend/src/app/packages/users/users.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN01 | US-AN06 | FR-AN21 | CA-010 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN03 | US-AN06 | FR-AN21 | CA-010 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN04 | US-AN06 | FR-AN21 | CA-010 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN05 | US-AN06 | FR-AN21 | CA-010 | Implementado | `frontend/src/app/packages/analytics/dashboard/dashboard.component.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN01 | US-AN06 | FR-AN22 | CA-011 | Implementado | `frontend/src/app/app.routes.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12D | DEP-04 | PKG-06 | CU-AN03 | US-AN06 | FR-AN22 | CA-011 | Implementado | `frontend/src/app/app.routes.ts` |
| 007 | OE-01 | OT-07 | OO-12 | M-12C | DEP-04 | PKG-06 | CU-AN01 | US-AN06 | FR-AN25 | CA-010 | Implementado | `backend/app/packages/analytics/services/stats_service.py` |
| 008 | OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM01 | US-PM01 | FR-PM07 | CA-001 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM01 | US-PM01 | FR-PM08 | CA-001 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM01 | US-PM01 | FR-PM21 | CA-001 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 008 | OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM05 | US-PM01 | FR-PM04 | CA-002 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 008 | OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM05 | US-PM01 | FR-PM16 | CA-002 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM04 | US-PM04 | FR-PM03 | CA-003 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 008 | OE-01 | OT-08 | OO-13 | M-13C | DEP-05 | PKG-07 | CU-PM06 | US-PM02 | FR-PM01 | CA-004 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 008 | OE-01 | OT-08 | OO-13 | M-13C | DEP-05 | PKG-07 | CU-PM06 | US-PM02 | FR-PM09 | CA-004 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13C | DEP-05 | PKG-07 | CU-PM02 | US-PM02 | FR-PM09 | CA-004 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13C | DEP-05 | PKG-07 | CU-PM02 | US-PM02 | FR-PM10 | CA-004 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM02 | FR-PM02 | CA-005 | Implementado | `backend/app/packages/analytics/routes/stats.py` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM02 | FR-PM12 | CA-005 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM02 | FR-PM22 | CA-005 | Implementado | `backend/app/packages/analytics/services/stats_service.py` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM03 | FR-PM11 | CA-006 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM03 | FR-PM13 | CA-006 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM03 | FR-PM14 | CA-005 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM03 | FR-PM15 | CA-007 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13D | DEP-05 | PKG-07 | CU-PM03 | US-PM06 | FR-PM17 | CA-008 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM07 | US-PM05 | FR-PM18 | CA-009 | Parcial | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM07 | US-PM05 | FR-PM19 | CA-009 | Parcial | `frontend/src/app/core/services/ui-preferences.service.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM07 | US-PM05 | FR-PM20 | CA-010 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM01 | US-PM06 | FR-PM05 | CA-011 | Implementado | `frontend/src/app/core/guards/engineer.guard.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM01 | US-PM06 | FR-PM06 | CA-011 | Implementado | `frontend/src/app/app.routes.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM01 | US-PM06 | FR-PM23 | CA-011 | Implementado | `frontend/src/app/packages/data-engineering/elt-pipeline/elt-pipeline.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13B | DEP-05 | PKG-07 | CU-PM01 | US-PM06 | FR-PM25 | CA-011 | Implementado | `frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.ts` |
| 008 | OE-01 | OT-08 | OO-13 | M-13A | DEP-05 | PKG-07 | CU-PM08 | US-PM07 | FR-PM24 | CA-012 | Implementado | `elt/pipelines/elt_pipeline.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE01 | US-DE01 | FR-DE01 | CA-001 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE01 | US-DE01 | FR-DE03 | CA-001 | Implementado | `backend/app/packages/analytics/services/analytics_service.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE01 | US-DE01 | FR-DE13 | CA-001 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE01 | US-DE01 | FR-DE14 | CA-001 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE02 | US-DE01 | FR-DE09 | CA-002 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE05 | US-DE01 | FR-DE15 | CA-003 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE03 | US-DE02 | FR-DE02 | CA-004 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE03 | US-DE02 | FR-DE04 | CA-004 | Implementado | `backend/app/packages/analytics/services/analytics_service.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14C | DEP-05 | PKG-07 | CU-DE03 | US-DE02 | FR-DE12 | CA-005 | Implementado | `backend/app/packages/analytics/services/analytics_service.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14C | DEP-05 | PKG-07 | CU-DE03 | US-DE02 | FR-DE11 | CA-005 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE04 | US-DE02 | FR-DE06 | CA-006 | Implementado | `backend/app/packages/analytics/services/analytics_service.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE04 | US-DE02 | FR-DE10 | CA-006 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE05 | US-DE02 | FR-DE07 | CA-005 | Implementado | `backend/app/packages/analytics/services/analytics_service.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14A | DEP-05 | PKG-07 | CU-DE06 | US-DE03 | FR-DE16 | CA-007 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14B | DEP-05 | PKG-07 | CU-DE07 | US-DE04 | FR-DE08 | CA-008 | Implementado | `frontend/src/app/core/guards/engineer.guard.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14B | DEP-05 | PKG-07 | CU-DE07 | US-DE04 | FR-DE18 | CA-008 | Implementado | `frontend/src/app/layouts/dashboard-layout/dashboard-layout.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14B | DEP-05 | PKG-07 | CU-DE07 | US-DE04 | FR-DE17 | CA-009 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14B | DEP-05 | PKG-07 | CU-DE01 | US-DE04 | FR-DE19 | CA-009 | Implementado | `frontend/src/app/packages/data-engineering/explorer/explorer.component.ts` |
| 009 | OE-01 | OT-09 | OO-14 | M-14D | DEP-05 | PKG-07 | CU-DE03 | US-DE04 | FR-DE21 | CA-009 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 009 | OE-01 | OT-09 | OO-14 | M-14C | DEP-05 | PKG-07 | CU-DE03 | US-DE02 | FR-DE05 | CA-010 | Implementado | `backend/app/packages/analytics/routes/analytics.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS01 | US-CS01 | FR-CS01 | CA-001 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS01 | US-CS01 | FR-CS16 | CA-001 | Implementado | `frontend/src/app/packages/streaming/artists/artists.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS01 | US-CS01 | FR-CS19 | CA-001 | Implementado | `frontend/src/app/packages/streaming/artists/artists.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS02 | US-CS01 | FR-CS02 | CA-002 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS02 | US-CS01 | FR-CS16 | CA-002 | Implementado | `frontend/src/app/packages/streaming/artists/artists.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16C | DEP-06 | PKG-02 | CU-CS03 | US-CS01 | FR-CS03 | CA-003 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16C | DEP-06 | PKG-02 | CU-CS03 | US-CS01 | FR-CS14 | CA-003 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS04 | US-CS02 | FR-CS04 | CA-004 | Implementado | `backend/app/packages/streaming/routes/genres.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS04 | US-CS02 | FR-CS17 | CA-004 | Implementado | `frontend/src/app/packages/streaming/genres/genres.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS05 | US-CS02 | FR-CS05 | CA-005 | Implementado | `backend/app/packages/streaming/routes/genres.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS06 | US-CS02 | FR-CS06 | CA-006 | Implementado | `backend/app/packages/streaming/routes/genres.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS07 | US-CS03 | FR-CS07 | CA-007 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS07 | US-CS03 | FR-CS18 | CA-007 | Implementado | `frontend/src/app/packages/streaming/tracks/tracks.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS08 | US-CS03 | FR-CS08 | CA-008 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16B | DEP-06 | PKG-02 | CU-CS09 | US-CS03 | FR-CS09 | CA-009 | Implementado | `backend/app/packages/streaming/routes/tracks.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS01 | US-CS04 | FR-CS20 | CA-010 | Implementado | `frontend/src/app/packages/streaming/artists/artists.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS01 | US-CS04 | FR-CS21 | CA-010 | Implementado | `frontend/src/app/packages/streaming/artists/artists.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16A | DEP-06 | PKG-02 | CU-CS01 | US-CS04 | FR-CS22 | CA-010 | Implementado | `frontend/src/app/packages/streaming/artists/artists.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16C | DEP-06 | PKG-02 | CU-CS03 | US-CS04 | FR-CS23 | CA-003 | Implementado | `frontend/src/app/packages/streaming/tracks/tracks.component.ts` |
| 010 | OE-01 | OT-09 | OO-16 | M-16D | DEP-06 | PKG-02 | CU-CS01 | US-CS05 | FR-CS15 | CA-011 | Parcial | `backend/app/packages/streaming/routes/artists.py` |
| 010 | OE-01 | OT-09 | OO-16 | M-16D | DEP-06 | PKG-02 | CU-CS01 | US-CS05 | FR-CS10 | CA-012 | Implementado | `backend/app/packages/streaming/routes/artists.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO01 | US-HO01 | FR-HO06 | CA-001 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO01 | US-HO01 | FR-HO08 | CA-001 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO01 | US-HO01 | FR-HO09 | CA-001 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO01 | US-HO01 | FR-HO11 | CA-002 | Implementado | `frontend/src/app/shared/services/stats.service.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17D | DEP-01 | PKG-05 | CU-HO02 | US-HO02 | FR-HO10 | CA-003 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17D | DEP-01 | PKG-05 | CU-HO02 | US-HO02 | FR-HO06 | CA-003 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17B | DEP-01 | PKG-05 | CU-HO04 | US-HO01 | FR-HO01 | CA-004 | Implementado | `backend/app/main.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17B | DEP-01 | PKG-05 | CU-HO04 | US-HO01 | FR-HO02 | CA-004 | Implementado | `backend/app/main.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17B | DEP-01 | PKG-05 | CU-HO04 | US-HO01 | FR-HO03 | CA-004 | Implementado | `backend/app/main.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17C | DEP-01 | PKG-05 | CU-HO04 | US-HO04 | FR-HO07 | CA-005 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17C | DEP-01 | PKG-05 | CU-HO04 | US-HO04 | FR-HO08 | CA-005 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17C | DEP-01 | PKG-05 | CU-HO04 | US-HO04 | FR-HO12 | CA-006 | Implementado | `frontend/src/app/packages/administration/settings/settings.component.ts` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO03 | US-HO03 | FR-HO04 | CA-007 | Implementado | `backend/app/main.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO05 | US-HO05 | FR-HO14 | CA-008 | Implementado | `docker-compose.yml` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO05 | US-HO05 | FR-HO15 | CA-008 | Implementado | `docker-compose.yml` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO05 | US-HO05 | FR-HO18 | CA-008 | Implementado | `backend/app/main.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO06 | US-HO05 | FR-HO16 | CA-009 | Implementado | `scripts/validate_warehouse.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO06 | US-HO05 | FR-HO17 | CA-009 | Implementado | `scripts/analyze_warehouse.py` |
| 011 | OE-01 | OT-10 | OO-17 | M-17A | DEP-01 | PKG-05 | CU-HO01 | US-HO01 | FR-HO19 | CA-010 | Implementado | `specs/011-health-operations/spec.md` |
