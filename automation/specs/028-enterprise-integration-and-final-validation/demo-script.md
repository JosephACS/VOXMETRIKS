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

1. **CRM → Prospects / Opportunities** — pipeline (seed or create)
2. **Quotations / Contracts** — show linked commercial record
3. **Subscriptions → Plans / My subscription** — entitlements
4. **Billing → Invoices** — list (MOCK labeled)
5. **Billing → Payment attempts / Reconciliation** — mock payment path

*Talking point:* MOCK payment; no real money. Billing 019 + CRM 017. UI uses active org context (`X-Organization-Id`).

## Act 4 — Catalog & campaigns (3 min)

1. **Artist Profiles** — business profile (not streaming `/artists`)
2. **Catalog Rights → Assets** — rights metadata
3. **Campaigns** — create campaign, show budget/ROI honest state

*Talking point:* ROI may show unavailable — honest UX from 022.

## Act 5 — Analytics, reporting & compliance (4 min)

1. **Business Analytics** dashboard — KPIs from warehouse
2. **Reports** — generate executive snapshot, approve, publish, export CSV (academic disclaimer)
3. **Business Decisions** — record decision linked to report
4. **Compliance** — terms list, DSR submit (synthetic)
5. **Platform Ops** — health endpoint shows `labeled_academic`

## Act 6 — Customer Success & Support (3 min)

1. **Customer Success** — calculate health (rule-based, not AI); show No disponible honesty if needed
2. **Support** — create ticket, internal note, resolve
3. **Renewal / Expansion** — evaluate renewal; create expansion opportunity

## Act 7 — Honest limits (1 min)

State explicitly:

- Royalties/Payouts OUT_OF_SCOPE (not Specs 024/025)
- MOCK payment/email; DuckDB academic; Playwright E2E not verified
- SLA configs are academic, not contractual

## Q&A references

- `deployment-limitations.md`
- `accepted-debt.md`
- `TRACEABILITY-MASTER.md`
