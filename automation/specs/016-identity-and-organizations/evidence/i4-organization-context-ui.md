# I4 — Organization context UI

**Status**: COMPLETE

## Store

`OrganizationContextService`:

- `organizations`, `activeOrganization`, `membership`, `roles`, `permissions`
- `loading` / `error` / `contextKind` (`none` | `active` | `invalid` | `access_revoked`)
- `bootstrap()` → GET list + GET current (revalidación)
- `activate(id)` → clear scoped state → POST activate → refresh list → apply new permissions
- **No** localStorage como fuente de autorización

## Selector

Integrado en `dashboard-layout` topbar (`app-org-selector`):

- org activa / loading / vacío
- lista solo de orgs del usuario
- crear organización
- suspended/closed → rutas dedicadas
- teclado: botón + menú focusable; `document:click` cierra

## Navegación

Sección sidebar `ORGANIZACIONES` (i18n ES/EN). Con org activa: settings, members, invitations, audit.
