# Demo Data Guide — Spec 028

How to populate and present honest demo/synthetic data.

## Built-in users

Seeded by `ensure_user_tables` on boot:

| Login | Password | Use |
|-------|----------|-----|
| `demo` | `demo123` | Standard user journey |
| `admin` | `admin123` | Platform admin, engineer routes |

## Warehouse data

1. Run ELT: `make pipeline` or `python analytics/elt/pipelines/elt_pipeline.py`
2. Source: PocketBase or `data/bronze/raw_spotify.parquet`
3. Boot test DB uses minimal `dim_track` / `fact_streaming` (pytest only)

## Enterprise demo seed (optional)

```bash
VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python apps/backend/scripts/seed_enterprise_demo.py
```

Creates:

| Entity | Identifier | Flags |
|--------|------------|-------|
| Organization | slug `enterprise-demo-s028` | `is_demo=TRUE` |
| Plan | code `demo-enterprise-starter` | description tagged SYNTHETIC |
| Subscription | trialing stub | `activation_source=demo_seed_synthetic` |

Safe if tables missing — skips with message.

## MOCK integrations

All labeled academic:

- **Payment:** `AcademicMockProvider` (billing)
- **Email/notifications:** console adapters (platform_ops)
- **Webhooks:** idempotent receive, no external HTTP

## What NOT to claim

- No real revenue, MRR, or customer counts
- No GDPR certification
- No licensed streaming catalog
- Royalties/payouts data — specs 024/025 absent

## Demo flow suggestions

See `demo-script.md` for presenter steps.

## Frontend demo indicators

- `isDemoUser` computed in dashboard layout (email `demo@` or plan `demo`)
- Platform ops health returns `labeled_academic: true`
