# I4 — Frontend architecture

**Spec**: 016 · **Stage**: I4 · **Status**: COMPLETE

## Package

`apps/frontend/src/app/packages/organizations/`

| Área | Ruta |
|------|------|
| Models | `models/organization.models.ts` |
| API client | `services/organizations-api.service.ts` |
| Context store | `services/organization-context.service.ts` |
| Guards | `guards/organization.guards.ts` |
| Routes | `organizations.routes.ts` → spread en `app.routes.ts` |
| Selector | `components/org-selector.component.ts` |
| Pages | `pages/org-*.page.ts` |
| Styles | `styles/organizations.css` |

## Ownership

- Auth permanece en `AuthService` / identity (no duplicado).
- Bearer via interceptor HTTP existente (`HttpClient`).
- No mocks de producción; errores tipados (`OrganizationsApiError`).

## Angular patterns

Standalone components, signals, lazy `loadComponent`, FormsModule para formularios.

## Fuera de alcance (respetado)

Billing, CRM, campañas, artistas empresariales, custom roles, email real, rediseño total.
