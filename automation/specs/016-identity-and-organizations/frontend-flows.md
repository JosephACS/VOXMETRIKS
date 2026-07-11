# Frontend Flows — Spec 016

**Status**: DESIGN_APPROVED · **IMPLEMENTED** (I4/I5)  
**Packages:** `identity` (reutilizado) · `organizations` (nuevo)

---

## Páginas

| Ruta | Estado |
|------|--------|
| `/organizations/new` | IMPLEMENTED |
| Shell org selector | IMPLEMENTED |
| `/organizations/onboarding` | IMPLEMENTED |
| `/organizations/:id/settings|members|invitations|roles|audit` | IMPLEMENTED |
| `/organizations/none|suspended|closed` · `/access-denied` | IMPLEMENTED |
| `/invitations/accept` | IMPLEMENTED (query/paste token; path-token removed I5) |

Responsive: stack forms; selector compacto en mobile.  
No pantallas billing/CRM/campaigns.

## Guards

`authGuard` + `organizationPathContextGuard` + `organizationPermissionGuard` (UX only; backend authority).

Playwright E2E: **NOT_VERIFIED** (I6).
