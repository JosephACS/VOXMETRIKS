# I5 — IDOR validation

**Status**: COMPLETE

## Pruebas (`test_organizations_security_i5.py`)

- Org A no lee/patch Org B → 404
- `member_id` de Org B bajo path Org A (remove/suspend/roles) → 404
- `invitation_id` de Org B bajo path Org A (revoke/resend) → 404
- Audit Org B con credenciales A → 404
- IDs arbitrarios → 404
- Path vs `X-Organization-Id` conflicto → 400

## Política

Anti-enum: recursos ajenos/inexistentes → **404**.  
Permiso insuficiente en org propia → **403**.

## Defensa en profundidad

UC usa `get_by_id_in_organization` / `MembershipNotFound` en lugar de PermissionDenied cross-org.
