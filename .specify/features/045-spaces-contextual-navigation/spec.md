# 045 — Espacios y navegación contextual

| Campo | Valor |
|-------|-------|
| **Feature** | `045-spaces-contextual-navigation` |
| **Estado** | Implementación v1 (FE) |
| **Fecha** | 2026-08-06 |
| **Git** | Prohibido en esta fase (gestión manual VS Code) |

---

## 1. Problema actual

La navegación se filtra principalmente por **rol de identidad** (`user` / `admin` / `engineer`) y, de forma separada, por **organización activa**. El usuario percibe “cambiar de rol” o pierde claridad al mezclar música personal, orgs, Data Ops y administración en un mismo menú basado en identity role.

No existe un **selector de espacios** unificado. El selector de organización cubre solo orgs. Los perfiles artísticos tienen tablas de asignación/equipo, pero **no** hay API “artistas míos”.

## 2. Alcance (v1)

- Modelo de espacios: Personal, Organización (N), Data Ops, Administración de plataforma.
- Tipos y arquitectura preparados para **Artista** sin mostrar datos inventados.
- Selector de espacios (protagonismo solo si hay >1 espacio).
- Navegación contextual por espacio activo (shell único).
- Persistencia segura del espacio + fallback a Personal.
- Reutilizar `OrganizationContextService` para espacios org.
- Actualizar `productSurfaceGuard` para permitir rutas comerciales de org **solo** cuando el espacio activo es Organización (sin borrar módulos).
- Pruebas unitarias de política y servicio.
- Documentación en `.specify`.

## 3. Fuera de alcance

- Borrado físico de módulos, tablas o endpoints.
- Simular espacios artísticos sin relación real.
- Convertir `user|admin|engineer` en roles de organización.
- Planes/checkout nuevos, anuncios, offline, eliminación CRM.
- Duplicar shell, sesión o reproductor.
- Operaciones Git.

## 4. Actores

| Actor | Espacios típicos |
|-------|------------------|
| Cuenta listener | Personal (+ orgs si membership) |
| Miembro de org | Personal + Organización(es) |
| Engineer / admin identity | + Data Ops |
| Admin identity / CRM `platform_admin` | + Administración de plataforma |
| Asignación artist team | Artista — **cuando exista API** |

## 5. Espacios

| Kind | Id estable | Aparece cuando | Home |
|------|------------|----------------|------|
| `personal` | `personal` | Siempre (autenticado) | `/discover` |
| `organization` | `org:{id}` | `GET /organizations` no vacío | `/organizations/{id}` |
| `artist` | `artist:{id}` | Relación real user↔artist (**API pendiente**) | TBD |
| `data_ops` | `data_ops` | `hasEngineerAccess()` | `/elt-pipeline` |
| `platform_admin` | `platform_admin` | identity `admin` **o** CRM `platform_admin` | `/platform-ops` |

## 6. Reglas de navegación

- Un solo `DashboardLayout` + player global.
- Al cambiar espacio: menú + contexto de datos (activar/limpiar org); **no** logout; **no** `stopPlayback`.
- El usuario **no** elige rol ni permisos; solo espacios autorizados.
- Módulos CRM genérico / CS / Compliance / Business Decisions: fuera del menú de espacios v1; rutas directas siguen existiendo (038 / product surface salvo excepciones org).

## 7. Seguridad

- Backend sigue siendo autoridad (org activate, RBAC, engineerGuard, platformAdminGuard, staffCapability).
- FE solo oculta/filtra UX; deep-links siguen gated.
- Espacio guardado inválido o membresía revocada → Personal.
- No se puede “seleccionar” un espacio no listado en `availableSpaces`.

## 8. Compatibilidad

- Presentation demos (`demo.business`, etc.) conservan menús especiales existentes.
- `OrganizationContextService` y preferencia server de org se reutilizan.
- Household `/account/profiles` **no** es un espacio de producto (sigue siendo who’s listening).

## 9. Criterios de aceptación

1. Usuario solo Personal: sin selector prominente (≤1 espacio) o solo Personal.
2. Usuario con 1+ orgs: espacios Personal + cada org; cambio activa org y menú org.
3. Engineer: aparece Data Ops; menú ELT/Explorer/reportes técnicos.
4. Admin / platform_admin: aparece Administración de plataforma.
5. Espacio inválido en storage → Personal.
6. Cambio de espacio no detiene el player.
7. Sin espacios artísticos inventados.
8. Compilación FE + tests relevantes en verde (o fallos reportados sin ocultar).

## 10. Plan de pruebas

- Unit: `space-access.policy.spec.ts`, `space-context.service` (persistencia/fallback).
- Unit: `classifyProductDeepLink` con espacio org (si se extiende).
- Manual: login roles + cambio espacio + play continuo.
- `ng test` / vitest según config del repo; `ng build`.

## 11. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Auto-activate de org única pelea con Personal | Tras bootstrap espacios, respetar espacio guardado; Personal llama `enterPersonalMode` |
| Reportes org_scoped sin org | Espacio org activa membership; Personal no debe abrir esos reportes en menú |
| productSurface permite campaigns en org | Solo con space kind organization; backend RBAC intacto |
| Artist API ausente | Lista vacía + deuda documentada |

## 12. Rollback lógico (sin Git)

1. Feature flag / no usar SpaceContext en layout (revertir imports del shell a menú por rol 043).
2. Quitar space-selector del HTML.
3. Restaurar productSurface sin `activeSpaceKind`.
4. Conservar archivos en `core/spaces` desconectados si hace falta diagnóstico.

## 13. Inventario técnico (PASO 2)

| Área | Archivos |
|------|----------|
| Shell | `layouts/dashboard-layout/*` |
| Nav policy | `core/navigation/nav-access.policy.ts` |
| Sesión | `core/services/auth.service.ts` |
| Org context | `packages/organizations/services/organization-context.service.ts` |
| Org selector | `packages/organizations/components/org-selector.component.ts` |
| Player | `shared/components/player-bar/*`, `playback-core/playback.store.ts`, `MusicPlayerService` |
| Guards | `auth`, `engineer`, `platform-admin`, `staff-capability`, `product-surface`, `organization.guards` |
| Rutas | `app.routes.ts` + `*.routes.ts` packages |
| CRM roles | `packages/crm/services/crm-context.service.ts` |
| Artists BE | `packages/artists` — assignments/team **sin** list-by-user |

## 14. Backend faltante (Artista)

No existe endpoint del estilo `GET /api/v1/artists/mine` que liste perfiles donde `app_artist_assignment` / `app_artist_team_member` vinculan al `user_id` actual.  
v1: `listArtistSpaces() → []` y no se muestran entradas Artist en el selector.

## 15. Corrección Fase 1 (2026-08-07)

Ver [phase1-correction.md](./phase1-correction.md):

- productSurfaceGuard ya estaba wired vía `withProductSurfaceGuard`; se extrajo helper + tests de contrato.
- Nav Organización filtrada por `organizationModuleGuard` permissions/tiers reales.
- Platform Admin sin `/users` (perfil) ni `/business` (marketing).
- Data Ops visible para admin+engineer por `hasEngineerAccess()` (sin cambio de roles).
