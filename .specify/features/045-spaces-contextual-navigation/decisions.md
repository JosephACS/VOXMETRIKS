# 045 — Decisiones de implementación (espacios)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-08-06 |
| **Spec** | [spec.md](./spec.md) |

## Decisiones

1. Un solo shell (`DashboardLayout`); la nav cambia por `SpaceContextService.activeSpace`.
2. Organización reutiliza `OrganizationContextService.activate` / `enterPersonalMode`.
3. Artista: tipos + nav preparados; `artistMemberships = []` hasta API `artists/mine`.
4. Rol identity ≠ espacio: Data Ops / Platform Admin se derivan de capacidades globales, no se eligen como “rol”.
5. `productSurfaceGuard` permite rutas comerciales de org solo si `activeSpaceKind === 'organization'`.
6. Selector visible solo si `availableSpaces.length > 1`.
7. Persistencia: `localStorage.voxmetriks_active_space_v1`; logout la borra.
8. Cambio de espacio **no** llama `stopPlayback` (solo logout lo hace).

## Módulos retirados del menú por espacio (siguen por URL)

| Módulo | Rutas directas | Nota |
|--------|----------------|------|
| CRM genérico | `/crm/*` | productSurface → module-unavailable (salvo presentation) |
| Customer Success | `/customer-success`, `/support` | idem |
| Compliance | `/compliance/*` | idem |
| Business Decisions | `/business-decisions` | idem |
| Business Analytics standalone | `/business-analytics` | idem |

En espacio Organización sí se muestran Campaigns/Billing/Royalties/Subscriptions vía nav contextual + excepción productSurface.
