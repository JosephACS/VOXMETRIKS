# Spec 049 — TAF14 strategic AGG closure

**Status:** active  
**Branch:** `feature/049-taf14-strategic-agg-closure`  
**Package:** extend `business_analytics` (no new domain)

## Goal

Close TAF 14 functionally inside VOXMETRIKS:

1. OPERATIVE complete (preserve existing processes, Workpanel, 33 simple reports).
2. TACTICAL complete (preserve catalog, 8 complex reports, campaign-roi non-certified, Airflow intact).
3. STRATEGIC AGG complete — longitudinal read model, eight official objectives, honest provenance, and KPI → evidence → report → human decision → action → follow-up.

## Canonical chain

```text
proceso operativo → informe táctico → KPI/AGG → evidencia → reporte → decisión humana → acción → seguimiento
```

## Out of scope

- Strategic AI / LLM recommendations (`is_ai` remains false; rule-based only).
- Airflow / canonical ELT rewrite.
- Invented clients, goals, SLA, churn, ROI certification, FX conversion, real payouts.
- Duplicate dashboard module or parallel domain package.
- Mutations of the canonical DuckDB warehouse during tests.

## Read model

Table `agg_strategic_kpi_period` (idempotent by org-scope + objective + kpi + period):

| Field | Notes |
|-------|--------|
| organization_id | NULL only for platform-global metrics |
| objective_code | OE-01 … OE-08 |
| kpi_code | Reused existing codes when possible |
| period_start / period_end | Inclusive period bounds |
| value | NULL when unknown — never coerce to zero |
| unit | Display unit |
| source_label | Provenance |
| quality_status | Honest quality code |
| is_synthetic / is_proxy | Classification flags |
| availability_status | available / unavailable / partial |
| unavailable_reason | Honest reason when no value |
| computed_at | Refresh timestamp |

## Official objectives

| Code | Title | Source rule |
|------|-------|-------------|
| OE-01 | Aumentar organizaciones activas | Orgs / memberships / subscriptions; globals Platform Admin only |
| OE-02 | Generar ingresos recurrentes | Reuse `active_mrr` / `active_arr`; multi-currency, no FX |
| OE-03 | Mejorar renovación | `past_due_mrr` + real CS/renewal signals; no renewal_rate/churn without valid denominator |
| OE-04 | Demostrar valor mediante ROI | Reuse `campaign_roi`; missing attribution → unavailable (never zero) |
| OE-05 | Aumentar adopción | Available activity/adoption; propagate synthetic/proxy from academic warehouse |
| OE-06 | Garantizar calidad de datos | Quality results, freshness, `ctl_pipeline_stages` |
| OE-07 | Proteger información empresarial | Sessions, RBAC, audit, incidents evidence — no invented security % |
| OE-08 | Mantener sostenibilidad operativa | Health, jobs, operational incidents — no undefined SLA claims |

## API / RBAC

- Extend `/api/v1/business-analytics` with strategic refresh + overview.
- Org isolation: org A never reads org B.
- Platform-global rows: Platform Admin only.
- Listener without permissions: denied without leaking sensitive data in errors.
- Overview always returns OE-01…OE-08 in order with decision capability flags.

## Frontend

Consolidate the existing business-analytics dashboard (no second screen):

- Header “Dirección estratégica”.
- Compact period summary + eight objective cards.
- Badges: Real / Sintético / Proxy / Simulado / No disponible.
- Trend only with ≥2 comparable periods.
- Links to evidence/report; draft executive report; continue to BusinessDecision.
- Responsive at 1366×768 and 390×844.
- No “IA” label on business recommendations.

## Acceptance (TAF 14)

- Operative + tactical surfaces remain navigable and intact.
- Existing warehouse AGG catalog preserved (documented 16/17 tables unchanged by this package).
- New strategic read model + eight visible objectives + seven reused KPIs (`total_streams`, `daily_streams`, `skip_rate`, `campaign_roi`, `active_mrr`, `active_arr`, `past_due_mrr`).
- Report → decision → action → follow-up path remains functional.
