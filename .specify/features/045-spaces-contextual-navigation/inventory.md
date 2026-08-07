# 045 — Inventario de archivos tocados

## Nuevos

| Archivo | Rol |
|---------|-----|
| `.specify/features/045-spaces-contextual-navigation/spec.md` | Spec |
| `.specify/features/045-spaces-contextual-navigation/decisions.md` | Decisiones |
| `apps/frontend/src/app/core/spaces/space.models.ts` | Tipos |
| `apps/frontend/src/app/core/spaces/space-access.policy.ts` | Política pura |
| `apps/frontend/src/app/core/spaces/space-access.policy.spec.ts` | Tests |
| `apps/frontend/src/app/core/spaces/space-nav.config.ts` | Nav por espacio |
| `apps/frontend/src/app/core/spaces/space-nav.config.spec.ts` | Tests |
| `apps/frontend/src/app/core/spaces/space-context.service.ts` | Servicio |
| `apps/frontend/src/app/core/spaces/index.ts` | Barrel |
| `apps/frontend/src/app/core/guards/product-surface.policy.ts` | Decisiones puras 038/045 |
| `apps/frontend/src/app/core/guards/product-surface.routes.ts` | prependRouteGuard + lista packages |
| `apps/frontend/src/app/core/guards/with-product-surface-guard.ts` | Wrapper usado por app.routes |
| `apps/frontend/src/app/core/guards/product-surface.guard.spec.ts` | Tests wiring + deep links |
| `.specify/.../phase1-correction.md` | Corrección Fase 1 |

## Modificados

| Archivo | Cambio |
|---------|--------|
| `layouts/dashboard-layout.component.ts` | Bootstrap spaces, nav contextual, logout clear |
| `layouts/dashboard-layout.component.html` | `app-space-selector` |
| `core/guards/product-surface.guard.ts` | Excepción por espacio activo |
| `core/services/auth.service.ts` | Limpia storage de espacio en logout |
| `core/i18n/locales/es.ts` / `en.ts` | Claves `spaces.*` |
| `.specify/feature.json` | Apunta a 045 |

## No modificados (reutilizados)

Auth, OrganizationContext, CrmContext, player-bar, PlaybackStore, engineer/platform/staff guards, rutas package (sin borrar módulos).
