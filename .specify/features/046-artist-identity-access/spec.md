# Spec 046 — Artist Identity & Access

## Resumen

Habilitar **Artist Spaces** basados en membresía real: un usuario solo ve y opera un espacio de artista si tiene `app_artist_membership` activa. Flujos de claim/access/create_new, invitaciones, y revisión Platform Admin.

## Actores

- **Applicant**: usuario autenticado que solicita propiedad, acceso o nuevo artista.
- **Owner / Administrator**: gestiona equipo, aprueba `request_access`, edita perfil.
- **Member / Reader**: lectura según permisos.
- **Platform Admin**: identity `admin` o CRM `platform_admin`; aprueba `claim_ownership` y `create_new` sin auto-membresía.

## Historias

1. Como usuario, listo mis Artist Spaces (`GET /artist-space/mine`) y activo uno sin cambiar mi rol identity ni detener el player.
2. Como owner/admin, invito, revoco y cambio roles (no owner vía invite; no promover a owner; no revocar último owner).
3. Como applicant, solicito claim / access / create_new; pending no crea membresía.
4. Como Platform Admin, reviso requests de claim/create_new.
5. Como owner/admin del artista target, apruebo `request_access`.

## Reglas de claim

| Tipo | Condición | Aprobador | Efecto |
|------|-----------|-----------|--------|
| `claim_ownership` | Warehouse artist existe; sin owner activo (o perfil sin owner) | Platform Admin | Crea/linkea perfil + membership owner |
| `request_access` | Perfil con owner | Owner/admin del artista | Membership con `proposed_role` ≠ owner |
| `create_new` | Nombre propuesto | Platform Admin | Perfil `org_id=0`, applicant = owner; `warehouse_artist_id` may be NULL; **no** auto `dim_artista` (explicit debt) |

## Capacidades por rol

| Permiso | owner | administrator | member | reader |
|---------|-------|---------------|--------|--------|
| `artist_space.view` | ✓ | ✓ | ✓ | ✓ |
| `artist_space.profile.update` | ✓ | ✓ | | |
| `artist_space.team.manage` | ✓ | ✓ | | |
| `artist_space.access.review` | ✓ | ✓ | | |
| `artist_space.invite` | ✓ | ✓ | | |

## Fuera de alcance

- Monetización / royalties en nav artist (Spec 047+).
- Email real de invitaciones (token copyable, `email_delivery_status=not_sent`).
- Sobrecargar assignment/team_member/portal_access como membership.
