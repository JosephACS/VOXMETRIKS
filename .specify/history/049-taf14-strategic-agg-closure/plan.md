# Plan 049 — TAF14 strategic AGG closure

## Architecture decision

Reuse `business_analytics` as the strategic surface. Warehouse `agg_*` catalog stays untouched. New longitudinal read model `agg_strategic_kpi_period` lives beside Spec 023 app tables and is refreshed from existing formulas (`compute_recurring_revenue`, campaign ROI snapshots, warehouse KPIs, quality/ctl/audit/health probes).

```text
sources (subs, campaigns, warehouse, ctl, audit, health)
        ↓ transactional refresh
agg_strategic_kpi_period
        ↓ overview API (RBAC)
BizAnalyticsDashboardPage (Dirección estratégica)
        ↓ evidence / report draft
ExecutiveReport → BusinessDecision → action → follow-up
```

## Backend design

1. **Schema** — `ensure_business_analytics_tables` creates `agg_strategic_kpi_period` idempotently (`CREATE TABLE IF NOT EXISTS` + lookup index). Logical idempotent key = `(COALESCE(organization_id,-1), objective_code, kpi_code, period_start, period_end)` enforced by transactional DELETE+INSERT (DuckDB ART unique indexes reject re-insert of deleted keys).
2. **Refresh** — `StrategicAggRefresh` deletes period+scope rows then inserts computed rows inside a DuckDB transaction; failure rolls back; never stores `0` for unknown.
3. **OE mapping** — one primary KPI row per objective (plus currency-scoped OE-02 rows when multi-ccy). Global OE-01/OE-08 platform metrics use `organization_id IS NULL`.
4. **Overview** — always eight objectives; includes period, source, quality, synthetic/proxy, availability, reason, evidence path, `can_create_decision` / `can_draft_report`.
5. **Reporting bridge** — executive snapshot payload includes strategic AGG rows for the generation period when present (immutable once frozen).
6. **RBAC** — org overview requires `biz_analytics.view`; global metrics require platform admin; cross-org reads impossible by query filter.

## Frontend design

1. Extend models + API client for strategic overview/refresh.
2. Consolidate `BizAnalyticsDashboardPage`: strategic header, eight OE cards, classification badges, empty/unavailable states, links to reports/decisions, keep commercial snapshot secondary.
3. i18n ES/EN keys for OE titles and badges.
4. Component styles via existing `.vx-enterprise` tokens; responsive grid.

## Test plan

- Temp DuckDB only; hash-check canonical warehouse before/after.
- Schema idempotency, refresh dedupe, rollback, isolation, null≠0, synthetic/proxy, multi-ccy no FX, ROI unavailable, eight OE overview, report snapshot, decision lifecycle.
- Frontend: API service + dashboard component directed specs; lint/test/build.

## Risks / honesty

- OE-03/05/07/08 may legitimately be unavailable without inventing denominators.
- Campaign ROI remains non-certified / simulated monetary semantics.
- Existing 16–17 warehouse aggregates are preserved; this package does not rebuild Gold AGG.
