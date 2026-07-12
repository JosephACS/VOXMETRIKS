# Deployment Limitations — Spec 028

Honest constraints for academic/demo deployment.

## Infrastructure

| Limitation | Impact |
|------------|--------|
| Single DuckDB file | No horizontal scale; write lock |
| No managed Postgres | Enterprise tables co-located with analytics |
| Docker compose optional | **NOT_VERIFIED** as CI gate |
| No K8s/Helm manifests | Manual deployment only |
| No CDN for SPA | `npm build` → static serve manual |

## Integrations

| Limitation | Impact |
|------------|--------|
| MOCK payment provider | No real charges |
| MOCK email | Console only |
| No Stripe/PayPal live keys | By design |
| Webhooks academic | No outbound production URLs |

## Compliance & legal

| Limitation | Impact |
|------------|--------|
| No GDPR certification | DSR tooling is demo-grade |
| No SOC2 / ISO claims | Out of scope |
| Terms/privacy are synthetic | Compliance module for workflow demo |
| No geo data residency | Single file DB |

## Product scope

| Limitation | Impact |
|------------|--------|
| Streaming not licensed service | YouTube/Audius/demo audio |
| Royalties (024) absent | No royalty accrual |
| Payouts (025) absent | No payout runs |
| CS / Support / Exec report deferred | 404 on API |
| Playwright E2E NOT_VERIFIED | Manual UI validation |

## Performance

| Limitation | Impact |
|------------|--------|
| No load testing | Unknown capacity |
| Background jobs single process | No distributed queue |
| ELT not incremental at scale | Full pipeline preferred |

## Suitable environments

- Local development
- Academic defense / portfolio demo
- CI unit/integration testing

## Not suitable for

- Production multi-tenant SaaS
- PCI-DSS payment processing
- Regulatory royalty distribution
