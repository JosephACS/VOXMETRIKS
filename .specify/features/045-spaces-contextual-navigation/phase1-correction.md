# 045 — Corrección de Fase 1 (post-revisión)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-08-07 |
| **Tipo** | Corrección — no nueva fase |
| **Git** | Sin operaciones Git en esta corrección |

---

## 1. productSurfaceGuard — integración real

### Hallazgo

El guard **sí estaba conectado** antes de esta corrección. En `app.routes.ts`, Spec 038 usa `withProductSurfaceGuard(...)` sobre:

- `CRM_ROUTES`, `SUBSCRIPTIONS_ROUTES`, `BILLING_ROUTES`, `ROYALTIES_ROUTES`
- `CAMPAIGNS_ROUTES`, `BUSINESS_ANALYTICS_ROUTES`, `COMPLIANCE_ROUTES`
- `REPORTING_ROUTES`, `CUSTOMER_SUCCESS_ROUTES`

**No** se aplica a:

| Paquete | Guard real |
|---------|------------|
| `PLATFORM_OPS_ROUTES` | `platformAdminGuard` |
| `ARTIST_PROFILES_ROUTES`, `CATALOG_*` | `organizationRequiredGuard` + `organizationModuleGuard` |
| `WORKPANEL` / simple / complex reports | `staffCapabilityGuard` |
| Música / personal / organizations | `authGuard` (+ org donde aplica) |

### Cambios en la corrección

- Extraído `withProductSurfaceGuard` → `core/guards/product-surface.routes.ts` (testeable).
- `decideProductSurfaceAccess` pura + excepción Spec 045 por espacio.
- Tests de wiring (helper + contrato de fuente `app.routes.ts`) y de decisiones deep-link.

### Deep links (política)

| Caso | Resultado |
|------|-----------|
| Personal → `/crm/*` | `module-unavailable` |
| Organización → `/campaigns|/billing|/royalties|/subscriptions` | allow (luego org RBAC) |
| Organización → `/crm` | `module-unavailable` (no está en allowlist comercial del espacio) |
| Data Ops → `/workpanel` como listener | `staff-block` → 403 |
| Presentation demos | allow (legacy 038) |

---

## 2. Navegación Organización — permisos

Ítems filtrados con `canAccessModule` / `requireStaff` alineados a `*.routes.ts`:

| Ítem | moduleKind | permission |
|------|------------|------------|
| Resumen | `org_admin_basic` | `organization.view` |
| Artistas / Catálogo / Lanzamientos / Campañas / Derechos | `operational` | *(ninguno en ruta — solo tier)* |
| Regalías | `operational` | `royalty.view` |
| Equipo | `org_admin_advanced` | `member.view` |
| Reportes | — | `requireStaff` (`staffCapabilityGuard`) |
| Suscripción | `onboarding` | `subscription.view` |
| Facturas | `recovery` | `invoice.view` |

**No inventados:** `campaign.manage` no está en `campaigns.routes.ts` (solo `operational`) → no se exige en nav.

Deuda: campañas/catálogo sin permission code en ruta → visible a cualquier membership `operational`; backend sigue autorizando mutaciones.

---

## 3. Platform Admin — ítems finales

| Ruta | ¿Por qué? |
|------|-----------|
| `/platform-ops` | Superficie real + `platformAdminGuard` |
| `/platform-ops/audio-unresolved` | Ops real |
| `/workpanel` | Staff real |
| `/reports` | Hub reportes staff |
| `/settings` | Configuración real |

**Eliminados del espacio:**

| Ruta | Motivo |
|------|--------|
| `/users` | Es **perfil del usuario** (`UsersComponent`), no admin global de usuarios |
| `/business` | Landing marketing “para empresas”, no admin de organizaciones |
| `/subscriptions/plans` | Catálogo comercial B2B, no panel de administración de planes |

**Deuda documentada:** no existe superficie FE de “admin users” global ni CRUD global de organizaciones de plataforma. Pendiente de producto futuro.

---

## 4. Data Ops / `hasEngineerAccess`

`AuthService.hasEngineerAccess()` = `role === 'admin' \|\| role === 'engineer'`.

Por el modelo global actual, el espacio **Data Ops aparece para admin e engineer**.  
Esta corrección **no** cambia roles globales (sin evidencia Spec de separar admin fuera de Data Ops).

---

## 5. Contaminación diff vs main (clasificación)

| Área | Clasificación |
|------|---------------|
| `core/spaces/*`, `space-selector`, `product-surface.guard*`, `.specify/features/045*` | **A/B — 045** (nuevo) |
| `dashboard-layout` cambios de spaces + bootstrap | **B — 045** sobre base 043 |
| `es.ts` / `en.ts` claves `spaces.*` | **B — 045** |
| `enterprise.es.ts` / `enterprise.en.ts` (status, billing, business, errors…) | **A — 043/044** (sin `spaces.*`; trabajo enterprise previo en el working tree / rama) |
| CSS layout / status-labels si vienen del commit 045 | Revisar: pueden ser **A** arrastrados o **B** colaterales del commit de feature |

**Acción:** no se revirtieron enterprise locales a ciegas (dependencias legítimas 043/044). No se detectó cambio accidental que debiera borrarse en esta corrección salvo los ítems Platform Admin incorrectos (corregidos).

---

## 6. Riesgos residuales

1. Org `operational` sin permission granular en campaigns/catalog → menú más amplio que el ideal; BE mitiga.
2. `productSurface` allow en org no sustituye `organizationModuleGuard` — si fallara el filtro nav, la ruta aún exige org+tier.
3. Admin identity sigue viendo Data Ops por `hasEngineerAccess`.

---

## 7. Relación 043 / 044 / 045

- **043:** shells por rol, hubs, UX.
- **044:** consolidación / claridad de datos.
- **045:** espacios contextuales + selector; reutiliza org context y product surface 038; corrección Fase 1 endurece permisos nav + Platform Admin honesto + tests de wiring.

---

## Self-contained FE closure (follow-up)

See `dependency-closure.md` and `self-contained.md`. Branch tip must include Spec 043/044 FE files imported by HEAD routes/guards; org commercial routes use `organizationRequiredGuard` + `organizationModuleGuard`.
