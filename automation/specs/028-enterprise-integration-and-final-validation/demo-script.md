# Demo Script — Spec 028

**Duration:** ~15 minutes  
**Audience:** Academic reviewers / stakeholders  
**Prerequisites:** API + FE running, ELT executed once

## Setup (before presenting)

```bash
make pipeline
cd apps/backend && uvicorn app.main:app --reload --port 8000
cd apps/frontend && npm start
# Optional:
VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python apps/backend/scripts/seed_enterprise_demo.py
```

## Act 1 — Music platform (2 min)

1. Login as `demo` / `demo123`
2. Navigate **Discover** → play a track (YouTube/demo audio)
3. Show **Dashboard** streaming analytics — emphasize warehouse-backed metrics

*Talking point:* Music UX is exploration + engagement events, not licensed streaming.

## Act 2 — Organization context (2 min)

1. Login as `admin` / `admin123`
2. Create or select organization via org selector
3. Show **Organizations → Members** and roles

*Talking point:* B2B tenant model from Spec 016.

## Act 3 — Commercial stack (4 min)

1. **Subscriptions → Plans** — catalog (platform admin)
2. **Billing → Invoices** — list/create (MOCK labeled)
3. **Billing → Reconciliation** — ledger view
4. **CRM → Prospects** — pipeline demo record

*Talking point:* MOCK payment; no real money. Billing 019 + CRM 017.

## Act 4 — Catalog & campaigns (3 min)

1. **Artist Profiles** — business profile (not streaming `/artists`)
2. **Catalog Rights → Assets** — rights metadata
3. **Campaigns** — create campaign, show budget/ROI honest state

*Talking point:* ROI may show unavailable — honest UX from 022.

## Act 5 — Analytics & compliance (3 min)

1. **Business Analytics** dashboard — KPIs from warehouse
2. **Compliance** — terms list, DSR submit (synthetic)
3. **Platform Ops** — health endpoint shows `labeled_academic`

*Talking point:* Privacy tooling demo-grade; no GDPR cert claim.

## Act 6 — Honest limits (1 min)

State explicitly:

- No Customer Success / Support / Executive reports (404)
- No Royalties/Payouts (024/025 absent)
- DuckDB academic limits; Playwright E2E not verified in CI

## Q&A references

- `deployment-limitations.md`
- `accepted-debt.md`
- `TRACEABILITY-MASTER.md`
