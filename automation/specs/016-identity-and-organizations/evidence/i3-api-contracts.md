# Spec 016 — I3 API contracts

**Fecha:** 2026-07-11  
**Estado:** PASS

Router: `presentation/router.py` bajo `/api/v1`.

| # | Method | Path |
|---|--------|------|
| 1 | POST | `/organizations` |
| 2 | GET | `/organizations` |
| 3 | GET | `/organizations/{id}` |
| 4 | PATCH | `/organizations/{id}` |
| 5 | POST | `/organizations/{id}/close` |
| 6 | GET | `/organizations/current` |
| 7 | POST | `/organizations/{id}/activate` |
| 8 | GET | `/organizations/{id}/members` |
| 9 | PATCH | `/organizations/{id}/members/{mid}` |
| 10 | POST | `/organizations/{id}/members/{mid}/remove` |
| 11 | POST | `/organizations/{id}/invitations` |
| 12 | GET | `/organizations/{id}/invitations` |
| 13 | POST | `/invitations/{token}/accept` |
| 14 | POST | `/organizations/{id}/invitations/{iid}/revoke` |
| 15 | POST | `/organizations/{id}/invitations/{iid}/resend` |
| 16 | GET | `/organizations/{id}/roles` |
| 16b | GET | `/organizations/{id}/permissions` |
| 17 | PUT | `/organizations/{id}/members/{mid}/roles` |
| 18 | GET | `/organizations/{id}/audit-log` |

Identity login/logout/`/me` **sin cambios**. Idempotencia create: slug-determinista (no Idempotency-Key persistente).
