# 046 — Decisiones

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-08-07 |
| **Spec** | [spec.md](./spec.md) |

## Decisiones

1. **Membership source of truth** = `app_artist_membership` únicamente.  
   `app_artist_assignment`, `app_artist_team_member` y `app_artist_portal_access` permanecen para roster org / publishing (Specs 020/031). **No** son fuente de Artist Space.

2. **Canonical music identity** = `dim_artista`. Management profile = `app_artist_profile` linked by `warehouse_artist_id`. No clonar identidades musicales.

3. **Independent artists**: `organization_id = 0` sentinel. FE `ArtistContextService` **nunca** llama `OrganizationContext.activate(0)`.

4. **Auth de Artist Space**: sesión identity (`require_user_id`); **sin** `X-Organization-Id`. Autorización = membership + permission codes.

5. **Platform Admin**: mirror `platformAdminGuard` — identity role `admin` **OR** CRM role `platform_admin` (`list_user_platform_roles`). Aprobar **no** auto-añade al admin como member.

6. **Invitations**: reutilizar `organizations.domain.invitation_token` helpers. Roles invite: `administrator|member|reader` (nunca `owner`). Token plaintext once; hash stored; honest “not emailed”.

7. **Uniqueness**: app-layer — una membership activa por `(artist_profile_id, user_id)`; un owner activo por artista.

8. **Tracks**: filtrar por `warehouse_artist_id` vía catálogo; si no hay link → lista vacía (nunca catálogo global).

9. **Nav artist (045 update)**: solo Resumen, Perfil, Música, Lanzamientos, Equipo. Sin royalties/billing/plan/ads.

10. **homePathForSpace(artist)** → `/artist-space`.

11. **DuckDB**: natural-key uniqueness en app layer (mismo patrón Spec 020); evitar UNIQUE secundario que rompa UPDATE.
