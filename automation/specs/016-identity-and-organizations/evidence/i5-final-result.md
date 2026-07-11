# I5 — Final result

**Stage I5**: COMPLETE  
**I6**: NOT STARTED  
**Spec 017**: NOT CREATED  
**Git**: no commands executed

## Vulnerabilidades encontradas → corregidas

| Issue | Fix |
|-------|-----|
| UPDATE child id without org in WHERE | `organization_id` en UPDATE membership/invitation; roles JOIN org |
| Invitation list via `member.view` | ACL invite/view only |
| Accept email oracle (403 vs 404) | mismatch → NotFound / 404 |
| NotFoundError → HTTP 400 | map to 404 |
| Preference stale after leave/remove | clear if matches |
| Technical `admin` as platform operator | removed; deny-by-default |
| FE token in path URL | route removed |
| Python pagination members/invites | SQL LIMIT/OFFSET |

## Validation

- pytest completo: **PASS** (incluye `test_organizations_security_i5.py`)
- FE: lint 0 errors · 77/77 tests · build OK (budgets warn preexistentes)
- Warehouse validate: OK · `app_user=5`
- E2E Playwright: **NOT_VERIFIED**

## Residual risks

- Deny-audit incompleto
- Elevated platform grants deferred
- Warehouse aún contiene orgs de sesiones anteriores (no creadas por I5)
- DuckDB concurrency limits
