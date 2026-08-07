# VOXMETRIKS — Propuesta de sistema de diseño unificado

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/design/voxmetriks-design-system-proposal.md` |
| **Fecha** | 2026-08-06 |
| **Estado** | Propuesta — **no crear componentes nuevos aún** |
| **Base existente** | `apps/frontend/src/app/shared/components/enterprise/*` + UI musical shared |
| **Specs** | 043 professional UX · 044 consolidation |

---

## 1. Principios de diseño

1. **Un producto, dos atmósferas controladas**
   - **Listener:** inmersión musical (player, covers, rails).
   - **Operativo (admin/engineer):** densidad de trabajo (CRUD, tablas, métricas).
   - Misma marca, tipografía y tokens; distinta densidad — no dos apps visuales distintas.

2. **Reutilizar antes de inventar**  
   El kit `enterprise-*` ya cubre ~70% del CRUD. Se mejora y se adopta; no se crea un segundo kit paralelo.

3. **Una composición por vista**  
   Listado = header + toolbar + tabla + estados. Sin dashboards decorativos dentro de CRUD.

4. **Honestidad de datos**  
   Badges visibles: `real` | `synthetic` | `simulated` | `mock` | `demo`.

5. **Accesibilidad y i18n de primera clase**  
   Toda cadena vía `t()` ES/EN; foco, contraste, labels en icon-only actions.

6. **Package-by-domain sin CSS por silo**  
   Dominios consumen primitives shared; no copian estilos de página en página.

7. **Excepción musical**  
   Track rows, player, media cards permanecen en shared musical — no forzar DataTable para listas de reproducción.

---

## 2. Inventario: qué ya existe

| Necesidad | Componente existente | Ruta | Acción |
|-----------|----------------------|------|--------|
| PageHeader | `EnterprisePageHeaderComponent` | `shared/components/enterprise/` | **Reutilizar** · renombrar alias opcional |
| CrudToolbar | `EnterpriseActionBarComponent` | idem | **Reutilizar** · ampliar slots search/filter |
| DataTable | `EnterpriseDataTableComponent` | idem | **Reutilizar** · estandarizar columnas/acciones |
| StatusBadge | `EnterpriseStatusBadgeComponent` | idem | **Reutilizar** |
| EmptyState | `EnterpriseEmptyStateComponent` + `EmptyStateComponent` | enterprise + shared | **Fusionar** → uno canónico |
| LoadingState | `EnterpriseLoadingSkeletonComponent` | enterprise | **Reutilizar** |
| ErrorState | `EnterpriseErrorStateComponent` | enterprise | **Reutilizar** |
| Form fields | `EnterpriseFormFieldComponent` | enterprise | **Reutilizar** |
| MetricCard | `EnterpriseStatCard` + `metric-card` + `kpi-card` | varios | **Fusionar** → MetricCard |
| Section/Card | `EnterpriseSectionCardComponent` | enterprise | Usar solo si aporta jerarquía; evitar cards decorativas |
| ConfirmDialog | `confirm-dialog` + service | shared | **Reutilizar** |
| OrgRequired | `EnterpriseOrgRequiredComponent` | enterprise | **Reutilizar** |
| Tables musicales | `table-widget`, `track-row` | shared | Mantener para música |
| Charts | `chart-widget` | shared | Mantener para reportes |
| Toasts | `notification-toast` | shared | **Reutilizar** |
| Permission | guards + `nav-access.policy` | core | No componente visual; documentar patrón |
| SearchInput | disperso en páginas | — | **Extraer** |
| FilterPanel | disperso | — | **Extraer** |
| Pagination | disperso / table interna | — | **Estandarizar** en DataTable |
| RowActions | inconsistente | — | **Estandarizar** menú ⋯ |
| FormDialog / FormPage | patrones por dominio | — | **Definir plantilla** |
| DetailPanel | parcial | — | **Definir plantilla** |

---

## 3. Estructura visual del shell

### 3.1 Layout principal

- **DashboardLayout** existente: sidebar + topbar + outlet + player (player solo contextos listener / cuando hay cola).
- Tokens: `shell-layout.tokens.ts` — **única fuente** de anchos sidebar, z-index, alturas header/player.

### 3.2 Sidebar

- Secciones por rol (ver role-audit).
- Ítem activo claro; grupos colapsables (ya hay persistencia localStorage).
- No mostrar secciones `DEMO_SECTION_IDS` en producto-final.

### 3.3 Header (topbar)

- Brand mark, breadcrumbs (módulo > vista), acciones globales (idioma, usuario, org selector).
- Evitar duplicar título de página en topbar y PageHeader — **PageHeader** lleva H1; breadcrumbs solo contexto.

### 3.4 Breadcrumbs

- Formato: `Área / Recurso / Detalle`.
- i18n keys, no strings hardcode.

### 3.5 Títulos y subtítulos

- H1: nombre del recurso (“Organizaciones”, “Prospectos” no en MVP).
- Subtítulo: una línea de propósito (máx. ~140 caracteres).
- Sin eye-brows decorativos ni badges flotantes sobre heroes musicales.

---

## 4. Tokens y look (dirección)

> Respetar UI existente 043; no imponer tema púrpura genérico ni cream/terracotta por defecto IA.

Propuesta de variables (nombres; valores a alinear con CSS actual):

```css
--vm-color-bg
--vm-color-surface
--vm-color-border
--vm-color-text
--vm-color-text-muted
--vm-color-accent          /* marca VOXMETRIKS existente */
--vm-color-success|warning|danger|info
--vm-radius-sm|md
--vm-space-1…6
--vm-font-sans             /* stack ya usado en 043 — no Inter por defecto si ya hay otra */
--vm-font-display          /* solo marketing/listener hero si aplica */
--vm-shadow-sm             /* mínimo; evitar multi-layer */
```

**Listener:** atmósfera con imagen/gradiente de catálogo donde ya exista.  
**Operativo:** superficie estable, alto contraste tabular, sin “glow”.

---

## 5. Componentes reutilizables objetivo

Alias de producto (implementación = enterprise existente + extracciones):

| Alias | Responsabilidad | Base |
|-------|-----------------|------|
| **PageHeader** | Título, subtítulo, primary action, optional secondary | enterprise-page-header |
| **CrudToolbar** | Search + filters toggle + bulk actions | enterprise-action-bar |
| **SearchInput** | Input debounce + clear + aria | **nuevo thin wrapper** |
| **FilterPanel** | Filtros aplicables/reset | **extraer** |
| **DataTable** | Columnas, sort, selection opcional, empty slot | enterprise-data-table |
| **StatusBadge** | Estados de entidad | enterprise-status-badge |
| **RowActions** | Ver / Editar / Eliminar / más | estandarizar en DataTable |
| **EmptyState** | Icono + mensaje + CTA | fusionar empties |
| **LoadingState** | Skeleton tabla/form | enterprise-loading-skeleton |
| **ErrorState** | Mensaje + reintentar | enterprise-error-state |
| **ConfirmDialog** | Destructive confirm | confirm-dialog |
| **FormDialog** | Create/edit modal pequeño | patrón nuevo sobre dialog existente |
| **FormPage** | Create/edit página completa | layout + form-field |
| **DetailPanel** | Cabecera + metadatos + relaciones | patrón |
| **Pagination** | Página/tamaño | parte de DataTable |
| **PermissionGate** | *ngIf / @if por permiso (UX only) | helpers org/crm + doc “BE authority” |
| **MetricCard** | KPI único | fusionar stat/kpi/metric |
| **DataSourceBadge** | real/synthetic/mock | data-source-badge existente |

**No construir** MetricCard/EmptyState nuevos si ya hay uno canónico tras fusión.

---

## 6. Plantilla estándar CRUD

### 6.1 Vista de listado

```
PageHeader (título, descripción, acción principal: “Crear”)
CrudToolbar (SearchInput, FilterPanel toggle, acciones secundarias)
DataTable
  ├─ columnas acordadas
  ├─ StatusBadge en columna estado
  ├─ RowActions
  └─ Pagination
Estados: LoadingState | EmptyState | ErrorState
```

Reglas:
- Una acción primaria máxima en header.
- Filtros solo si cambian el dataset (no filtros fantasma).
- Paginación obligatoria si N &gt; ~50.

### 6.2 Crear / Editar

**Preferir FormPage** para formularios &gt; 5 campos; **FormDialog** para 1–4 campos.

```
PageHeader / Dialog title
Form groups lógicos
EnterpriseFormField + validaciones visibles
Footer: Cancelar | Guardar (disabled si invalid | submitting)
```

Reglas:
- Prevención doble envío (`submitting` signal).
- Error de API bajo el form o toast + mensaje inline.
- Guard de salida si dirty (ConfirmDialog).
- No reset silencioso de errores.

### 6.3 Detalle

```
PageHeader + acciones permitidas (Editar, …)
Bloque información principal
StatusBadge
Metadatos (created/updated, ids internos colapsados)
Relaciones (links a entidades)
Historial solo si aporta (audit org/CRM — no en MVP listener)
```

### 6.4 Eliminar

ConfirmDialog con:
- Nombre del elemento
- Consecuencia (“No se puede deshacer” / dependencias)
- Validación de dependencias **en backend** (el dialog no es seguridad)
- Toast éxito / ErrorState

---

## 7. Estados visuales

| Estado | Componente | Notas |
|--------|------------|-------|
| Loading | LoadingState / skeleton | Evitar spinners genéricos sueltos en CRUDs |
| Empty | EmptyState + CTA | Copy i18n |
| Error | ErrorState + retry | Mensaje seguro (sin stack) |
| Denied | página 403 / org access-denied / module-unavailable | Ya existen rutas error |
| Mock data | DataSourceBadge | Obligatorio en dinero/simulado |
| Success | toast | No modal de éxito salvo casos legales |

---

## 8. Elementos de UI operativos

| Elemento | Convención |
|----------|------------|
| Botones | Primary / Secondary / Ghost / Danger — mismos tamaños en todo CRUD |
| Formularios | Labels arriba; help text; error bajo campo |
| Tablas | Densidad comfortable; hover fila; no zebra agresivo |
| Paginación | “Página X de Y” + tamaño |
| Buscadores | Debounce 300ms; Enter fuerza |
| Filtros | Panel lateral o barra; chip de filtros activos |
| Selectores | Mismo control; org selector ya en shell |
| Modales | Ancho fijo sm/md; foco trap |
| Alertas | Banner inline para warnings de página |
| Toasts | Esquina; auto-dismiss no critical |
| Badges | Status + DataSource solamente |
| Gráficos | Solo en reportes/Workpanel; paleta tokens |
| Menú contextual | Track context menu musical ≠ RowActions tabla |

---

## 9. Responsive

| Breakpoint | Comportamiento |
|------------|----------------|
| Desktop | Sidebar fijo / colapsable |
| Tablet | Sidebar overlay |
| Mobile | Sidebar drawer; tablas → card stack o scroll horizontal **consciente**; player full width |

CRUD admin: scroll horizontal de tabla aceptable; no esconder acciones críticas solo en hover (touch).

---

## 10. Accesibilidad

- Contraste AA en texto/botones operativos.
- `aria-label` en icon buttons (RowActions).
- Focus visible unificado.
- Dialogs: Escape cierra (si no dirty crítico).
- Tablas: headers scope; sort anunciado.
- No depender solo del color para estado (badge + texto).

---

## 11. Consistencia ES/EN

- Todas las cadenas de plantilla CRUD en `locales/es|en` + `enterprise.es|en`.
- Claves preferidas: `crud.list.title`, `crud.actions.create`, `crud.empty`, `crud.error.retry`, `crud.confirm.delete`, etc. (namespace a definir en implementación).
- Status labels centralizados (`status-labels.ts`).

---

## 12. Convenciones de nombres

| Tipo | Convención |
|------|------------|
| Componentes shared | `Vm` o `Enterprise` prefix existente — **no mezclar** en una misma PR; migrar gradualmente a un prefijo |
| Selectores | kebab-case alineado al archivo |
| i18n | `domain.view.element` |
| Rutas CRUD | `/{resource}`, `/{resource}/new`, `/{resource}/:id`, `/{resource}/:id/edit` cuando aplique |
| Permisos UI | mismo código que backend (`organization.view`) |

Recomendación: mantener prefijo `enterprise-*` en código hasta oleada de rename controlada; en docs de producto usar nombres PageHeader/DataTable.

---

## 13. Estrategia de migración de pantallas

### Fase 0 — Inventario de adopción
Listar páginas admin que **ya** usan enterprise-* vs HTML ad hoc.

### Fase 1 — Canonicar primitives
Fusionar EmptyState y MetricCard; documentar API pública del kit.

### Fase 2 — Migrar CRUDs MVP visibles
Orden sugerido:
1. Organizations (members/list)
2. Artist profiles list
3. Catalog-rights lists
4. Catalog-publishing lists / review inbox
5. Platform-ops tables (si se mantienen)

### Fase 3 — Reportes / Workpanel
Alinear headers y MetricCards; no forzar DataTable donde hay charts.

### Fase 4 — Listener
No migrar a enterprise table; solo alinear tokens tipográficos/colores y EmptyState musical.

### Fase 5 — Demos 038 (si algún día se reactivan)
Deben nacer ya sobre el kit — no invertir ahora.

**Regla:** una pantalla por PR/aprobación; sin big-bang.

---

## 14. Anti-patrones a eliminar gradualmente

- Cards decorativas en listados sin interacción.
- KPIs repetidos en cada CRUD.
- Botones primary múltiples.
- Modales de create con scroll infinito sin grupos.
- Copy hardcodeado ES-only.
- Ocultar acciones solo con CSS sin PermissionGate + BE deny.
- Skeletons que no coinciden con layout real.

---

## 15. Relación con la auditoría

- Clasificación UI: full-audit §16.
- Menús por rol: role-audit.
- Orden de ejecución: simplification-plan oleadas D/F.

---

## 16. Decisión requerida del usuario

Antes de implementar:

1. ¿Aceptar **enterprise kit** como sistema CRUD canónico?  
2. ¿Fusionar EmptyState y MetricCard en oleada temprana?  
3. ¿Priorizar migración Organizations → Catalog o al revés?  

**No se crearán componentes nuevos hasta aprobación explícita.**

---

**Fin propuesta de diseño.**
