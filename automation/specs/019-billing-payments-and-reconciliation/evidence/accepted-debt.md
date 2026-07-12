# Accepted debt — Spec 019

| Deuda | Impacto | Riesgo | Mitigación | Spec futura |
|-------|---------|--------|------------|-------------|
| Playwright E2E absent | No browser golden path | Medio | API/security suites | follow-up |
| platform_finance / platform_admin billing break-glass | Ops RBAC incomplete | Medio | Org billing perms work | hardening |
| FE orgId hardcoded placeholders | Wrong org if not wired | Medio | OrganizationContextService | FE polish |
| Webhook signature conceptual (env secret) | Not production-grade | Bajo | Documented academic | real provider |
| No real tax authority integration | Fiscal limited | Bajo | In scope exclusion | tax later |
| DuckDB not production ledger | Concurrency limits | Medio | Known constitution | PG future |
