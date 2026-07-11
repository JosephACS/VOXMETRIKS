# Spec 016 — I3 Cross-tenant security

**Fecha:** 2026-07-11  
**Estado:** PASS

Política anti-enumeración:

| Caso | HTTP |
|------|------|
| Org/member/invitation ajeno (sin membership) | **404** |
| Membership suspended | **403** `access_revoked` |
| Permiso insuficiente | **403** |
| member_id de otra org en path propio | **404** |

Queries organization-scoped en repos/use cases; no filtro post-hoc global.
