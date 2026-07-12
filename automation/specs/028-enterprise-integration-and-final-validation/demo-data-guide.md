# Demo Data Guide — Spec 028

How to populate and present honest demo/synthetic data.

## Built-in users

Seeded by `ensure_user_tables` on boot (credentials live in local seed/bootstrap only — not republished here):

| Login | Use |
|-------|-----|
| `demo` | Standard user journey |
| `admin` | Platform admin, engineer routes |
| `sales_agent@voxmetrik.io` | CRM agent (platform RBAC demo seed) |
| `sales_manager@voxmetrik.io` | CRM manager (platform RBAC demo seed) |

## Warehouse data

1. Run ELT: `make pipeline` or `python analytics/elt/pipelines/elt_pipeline.py`
2. Source: PocketBase or `data/bronze/raw_spotify.parquet`
3. Boot test DB uses minimal `dim_track` / `fact_streaming` (pytest only)

## Enterprise demo seed (optional)

```bash
cd apps/backend
VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python scripts/seed_enterprise_demo.py
```

Creates (all tagged demo/synthetic; skips missing tables gracefully):

| Entity | Identifier / notes | Flags |
|--------|--------------------|-------|
| Organization | slug `enterprise-demo-s028` | `is_demo=TRUE` |
| Plan + USD monthly price ($99) + active subscription with `plan_price_id` | `demo-enterprise-starter` | MRR-calculable |
| CRM | prospect → contact → opportunity → quotation → contract | SYNTHETIC |
| Billing | profile, invoice, payment mock; dunning recoverable via mock fail/retry | provider `academic_mock` |
| Artists / rights | artist profile, catalog asset, rights row | demo labels |
| Campaign | campaign + budget + expense | demo |
| Reporting | definition, generation, snapshot, executive report, decision | academic disclaimer |
| Customer Success | onboarding + health + risk + intervention | rule-based |
| Support | case + messages | demo |

Does **not** run on boot. Does **not** write warehouse facts.

## MOCK integrations

All labeled academic:

- **Payment:** `AcademicMockProvider` (billing)
- **Email/notifications:** console adapters (platform_ops)
- **Webhooks:** idempotent receive, no external HTTP

## What NOT to claim

- No real revenue, MRR, or customer counts
- No GDPR certification
- No licensed streaming catalog
- Royalties/payouts — **OUT_OF_SCOPE** (future; **not** Specs 024/025)

## Demo flow suggestions

See `demo-script.md` for presenter steps. Seed enables the full commercial → reporting → CS golden path when org schema is present.

## Frontend demo indicators

- `isDemoUser` computed in dashboard layout (email `demo@` or plan `demo`)
- Platform ops health returns `labeled_academic: true`
