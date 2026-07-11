# API Contracts — Spec 016

**Status**: DESIGN_APPROVED · **IMPLEMENTED** (I3/I5) · CLOSED_WITH_ACCEPTED_DEBT  
**Base:** `/api/v1` · Auth: Bearer session opaca

### Códigos HTTP

| Código | Uso |
|--------|-----|
| 400 | fuentes de contexto contradictorias; body inválido estructural |
| 401 | no autenticado |
| 403 | autenticado sin permiso / org suspended mutación |
| 404 | no encontrado, anti-enumeración cross-tenant, o invite email mismatch (anti-oracle I5) |
| 409 | conflicto (slug, duplicate member, last owner) |
| 410 | invitación expired/accepted/consumed |
| 422 | validación de campos/roles |

No DELETE físico de members/audit → soft state via PATCH/POST.

Idempotency-Key: **DEFERRED** (slug-deterministic create org only).  
Revoke invitation permission as-implemented: `invitation.revoke` (doc histórico también citaba `member.invite`).

---

## Endpoints (17)

| # | Method | Path | Permiso / actor | Context | Audit | Aislamiento |
|---|--------|------|-----------------|---------|-------|-------------|
| 1 | POST | `/organizations` | authenticated | crea | sí | n/a |
| 2 | GET | `/organizations` | authenticated | lista mías | no | solo memberships |
| 3 | GET | `/organizations/{id}` | organization.view | path | no | membership |
| 4 | PATCH | `/organizations/{id}` | organization.update | path | sí | membership |
| 5 | POST | `/organizations/{id}/close` | organization.close | path | sí | owner |
| 6 | GET | `/organizations/current` | authenticated | preferencia validada | no | — |
| 7 | POST | `/organizations/{id}/activate` | member active | path | sí | membership |
| 8 | GET | `/organizations/{id}/members` | member.view | path | no | yes |
| 9 | PATCH | `/organizations/{id}/members/{mid}` | member.suspend/update | path | sí | yes |
| 10 | POST | `/organizations/{id}/members/{mid}/remove` | member.remove | path | sí | soft removed |
| 11 | POST | `/organizations/{id}/invitations` | member.invite | path | sí | org active |
| 12 | GET | `/organizations/{id}/invitations` | member.invite\|view | path | no | yes |
| 13 | POST | `/invitations/{token}/accept` | authenticated invitee | token | sí | — |
| 14 | POST | `/organizations/{id}/invitations/{iid}/revoke` | member.invite | path | sí | yes |
| 15 | POST | `/organizations/{id}/invitations/{iid}/resend` | member.invite | path | sí | rotate token |
| 16 | GET | `/organizations/{id}/roles` | role.view | path | no | yes |
| 16b | GET | `/organizations/{id}/permissions` | role.view | path | no | yes |
| 17 | PUT | `/organizations/{id}/members/{mid}/roles` | role.assign | path | sí | yes |
| 18 | GET | `/organizations/{id}/audit-log` | audit.view | path | no | paginated |

*(18 contratos contando roles+permissions separados.)*

### Request/response (semántica)

- **Create org:** `{display_name, slug?, organization_type?, timezone?, default_currency?, country_code?, activate?: bool}` → `{organization, membership, roles}`  
- **Invite create:** `{email, role_codes[]}` → `{invitation_id, expires_at, invite_token?}` token solo modo académico  
- **Accept:** path token → `{membership, organization}`  
- **Errors negocio:** `slug_taken`, `last_owner`, `invite_expired`, `invite_revoked`, `already_member`, `email_mismatch`, `org_not_active`

### Paginación

members, invitations, audit-log: `page` + `limit` → envelope existente del proyecto.
