# 047 — Decisiones

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-08-07 |
| **Spec** | [spec.md](./spec.md) |
| **Base** | `7cba24d03cd83836a0ac0a88179735df7859102b` |

## Decisiones

1. **Recuperación selectiva**: solo paquetes/wiring necesarios para runtime demostrable (Workpanel, reports, listening, profile security, module access, sync catalog). No copiar el dirty tree completo.

2. **Preservar 046**: routers Artist Space / access / invitations (token en body) / platform artist-requests permanecen montados; tests 046 deben seguir en verde.

3. **Platform Admin ops access**: mirror Spec 046 / FE `platformAdminGuard` — identity role `admin` **OR** CRM `platform_admin` puede `ops.view` y `ops.manage`. **No** bypass para `ops.webhooks` / `ops.flags` / otros.

4. **Reportes org-scoped**: mantienen requisito `X-Organization-Id`; tests crean org/membresía válidas. No se debilitan a consultas globales.

5. **roles-permissions**: columnas `display_name` (no `name`) en `app_platform_role` / `app_business_role`; `COALESCE(r.display_name, r.code)`.

6. **Household profiles**: listado seguro (sin email / login hints); `prepare-switch` solo devolves `login_hint` + display; nunca sesión/token; plan inactivo limita a perfil `is_me`.

7. **Unified Music Search = DEFERRED / REQUIRES PRODUCT DECISION**
   Recuperar el servicio completo implica endpoints y escrituras de catálogo para listeners no aprobadas en Spec 047.
   - Se retira `tests/test_music_search_playable.py` (huérfano).
   - **No** se copia `music_search_service.py` ni cambios dirty de `catalog/routes/tracks.py`.
   - Se conserva `playback_availability.py` solo como dependencia de listening.

8. **Frontend test gate**: solución mínima tipados Node (`@types/node` + `tsconfig.spec.json`) y refactor ESM de specs que usaban `require`/`__dirname`. No excluir tests ni reducir el script `npm test`.

9. **Sin git publish en esta fase**: 0 staged forzado por proceso, 0 commit, 0 push, 0 merge hasta instrucción explícita.

10. **Checkout principal dirty**: solo lectura; nunca modificarlo desde este worktree.
