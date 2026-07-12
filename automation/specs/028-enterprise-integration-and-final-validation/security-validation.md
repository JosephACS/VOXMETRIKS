# Security Validation — Spec 028

**Scope:** Cross-cutting security posture at enterprise closure. No penetration test; pytest security suites per domain.

## AuthN / AuthZ

| Control | Status | Evidence |
|---------|--------|----------|
| JWT bearer on protected routes | **VERIFIED** | Per-domain 401 tests |
| Org header `X-Organization-Id` on tenant APIs | **VERIFIED** | campaigns, compliance, biz-analytics 400 without header |
| Cross-tenant isolation | **VERIFIED** | organizations I3, catalog_rights N5, billing L5 |
| Platform RBAC (`platform_admin`, `ops.*`) | **VERIFIED** | subscriptions K*, platform_ops R5 |
| Engineer-only explorer/warehouse | **VERIFIED** | `route_policy.py`, analytics security tests |
| Rate limiting (configurable off in tests) | **VERIFIED** | conftest sets limits to 0 |

## Data protection

| Control | Status | Notes |
|---------|--------|-------|
| Secret redaction in platform_ops API | **VERIFIED** | R3/R5 tests |
| No raw payment secrets in DB | **VERIFIED** | `secret_ref` only |
| Password bcrypt + legacy SHA-256 | **VERIFIED** | identity package |
| GDPR certification | **OUT_OF_SCOPE** | Privacy/DSR tooling only |
| Automated warehouse PII purge | **DEFERRED** | 026 accepted debt |

## Integration security

| Control | Status | Notes |
|---------|--------|-------|
| Webhook idempotency | **VERIFIED** | platform_ops R3 |
| MOCK payment provider labeled | **VERIFIED** | billing + platform_ops |
| MOCK email/console labeled | **VERIFIED** | platform_ops |
| CORS configurable | **VERIFIED** | `CORS_ORIGINS` env |

## Gaps (accepted)

- Playwright security UX flows: **NOT_VERIFIED**
- `platform_finance` break-glass: **DEFERRED** (019 debt)
- Production WAF / TLS termination: **OUT_OF_SCOPE** (academic deployment)
- CSRF on SPA: mitigated by bearer token; formal audit **NOT_VERIFIED**

## Recommended manual checks

1. Login as `demo` — confirm no `/platform-ops` write without role.
2. Attempt cross-org campaign read with wrong `X-Organization-Id` — expect 403/404.
3. Confirm `/health` does not leak DB path (default `HEALTH_VERBOSE=false`).
