# 046 — Inventario (exploración previa)

## Modelo de producto (aprobado)

| Concepto | Significado |
|----------|-------------|
| User | Persona (identity) |
| Space | Contexto de producto |
| Membership | Acceso real a un Artist Space |
| Role | Nivel (`owner` / `administrator` / `member` / `reader`) |
| Permission | Acción (`artist_space.*`) |

- Artist Space **solo** desde membresía real (`app_artist_membership` activa).
- Identidad musical canónica = `dim_artista` (warehouse).
- Perfil de gestión = `app_artist_profile` (Spec 020).
- Link: `warehouse_artist_id`. No duplicar identidades musicales.
- Artistas independientes: `organization_id = 0` (sentinel). Nunca activar `OrganizationContext` con `0`.

## Backend existente (reutilizar)

| Archivo | Rol |
|---------|-----|
| `apps/backend/app/packages/artists/infrastructure/schema.py` | `ensure_artist_tables`, `ARTISTS_TABLES` (6 tablas Spec 020) |
| `apps/backend/app/packages/artists/application/use_cases.py` | Perfiles org-scoped; `_next_id`, `_update_profile_row` |
| `apps/backend/app/packages/artists/presentation/router.py` | `/api/v1/artists` (requiere `X-Organization-Id`) |
| `apps/backend/app/packages/artists/presentation/dependencies.py` | `require_org_artist_permission` |
| `apps/backend/app/packages/organizations/domain/invitation_token.py` | `generate_invitation_token`, `hash_invitation_token`, `verify_invitation_token` |
| `apps/backend/app/packages/organizations/infrastructure/schema.py` | Patrón `app_organization_invitation` |
| `apps/backend/app/packages/organizations/application/use_cases/invitations.py` | Create/accept/revoke invite |
| `apps/backend/app/packages/catalog/routes/artists.py` | `GET /api/v1/catalog/artists?search=` (homónimos) |
| `apps/backend/app/packages/catalog/services/tracks/queries.py` | Filtro tracks por `artist_id` → `dim_artista` |
| `apps/backend/app/packages/catalog_publishing/` | Releases por `artist_profile_id` |
| `apps/backend/app/packages/identity/services/auth_deps.py` | `require_user_id`, `require_admin_user` |
| `apps/backend/app/packages/platform_rbac/infrastructure/repository.py` | `list_user_platform_roles`, `has_permission` |
| `apps/backend/app/main.py` | Registro de routers bajo `/api/v1` |
| `apps/backend/tests/test_artists_*.py` | Patrones schema/API/security |
| `apps/backend/tests/test_organizations_api_i3.py` | Auth headers + isolation |

## Tablas Spec 020 que NO son fuente de Space membership

| Tabla | Uso real |
|-------|----------|
| `app_artist_assignment` | Roster org / managers |
| `app_artist_team_member` | Equipo org-scoped |
| `app_artist_portal_access` | Portal publishing (Spec 031) |

## Frontend existente (045 + org)

| Archivo | Estado 046 |
|---------|------------|
| `core/spaces/space-context.service.ts` | `artistMemberships=[]`, `artistBackendMissing=true` |
| `core/spaces/space-nav.config.ts` | case `artist` con royalties/settings — reemplazar |
| `core/spaces/space.models.ts` | `homePathForSpace(artist)` → `/artist-profiles/...` — cambiar a `/artist-space` |
| `core/spaces/space-access.policy.ts` | Ya soporta `artistMemberships` reales |
| `core/guards/platform-admin.guard.ts` | identity admin OR CRM `platform_admin` |
| `packages/organizations/guards/` | Patrón `*RequiredGuard` / permission guard |
| `packages/artists/` | Org profiles (020) — no confundir con Artist Space |
| `packages/platform-ops/` | Nav + `platformAdminGuard` |

## Huecos a implementar

1. Tablas: `app_artist_membership`, `app_artist_access_request`, `app_artist_invitation`.
2. Routers sin `X-Organization-Id`: `/artist-space/*`, `/artist-access/*`, `/artist-invitations/*`, `/platform/artist-requests/*`.
3. `ArtistContextService` + guards + páginas Artist Space.
4. Wiring `SpaceContextService` → `GET /artist-space/mine`.
5. Claim wizard (Account/settings) + accept invite + platform requests page.
6. Tests BE isolation A–K + FE vitest + `ng build`.
