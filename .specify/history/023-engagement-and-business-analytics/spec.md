> **Status:** HISTORICAL_RECONSTRUCTED
> **Original spec.md:** no disponible en Git
> **Reconstruction sources:** d2f6a27f:automation/specs/023-engagement-and-business-analytics/evidence/spec-closure.md; accepted-debt.md; packages business_analytics/engagement; docs/STATUS.md
>
> Aviso: este documento reconstruye intención histórica a partir de evidencia disponible.
> No moderniza retrospectivamente el diseño original ni afirma runtime completo.
> La verdad vigente de producto está en [`docs/STATUS.md`](../../../docs/STATUS.md).

# Spec 023 — Engagement and Business Analytics

**ID:** 023
**Title:** Engagement and Business Analytics
**Status:** HISTORICAL_RECONSTRUCTED

## Objetivo histórico reconstruido

Capa empresarial de business analytics sobre métricas del warehouse existentes (catálogo KPI), sin segunda plataforma analítica, con recomendaciones solo rule-based (`is_ai=false`).

## Actores

- Analistas / staff con `biz_analytics.view|manage|alert`
- Consumidores de alertas y preferencias de vista

## Alcance

- Tablas: `app_kpi_definition`, `app_kpi_snapshot`, `app_metric_source`, `app_data_quality_result`, `app_business_alert`, `app_analytics_view_preference`, `app_recommendation_record`
- Envoltorio de métricas warehouse existentes

## Fuera de alcance

- ML/LLM recommendations
- Segunda plataforma de analytics
- Trends/comparatives completos (stubs en el cierre)

## Reglas de negocio demostrables

1. No inventar KPIs sin fuente.
2. Recomendaciones `is_ai=false` (reglas locales).
3. Subscription usage KPI depende de datos Spec 018 cuando existan.

## Casos de uso recuperables

1. Consultar definiciones/snapshots KPI.
2. Gestionar alertas de negocio.
3. Preferencias de vista analítica.
4. Recomendaciones rule-based.

## Criterios de aceptación verificables

- Paquetes `business_analytics` / `engagement` presentes.
- `docs/STATUS.md`: Business analytics / engagement = **parcial**.
- Cierre histórico: CLOSED_WITH_ACCEPTED_DEBT (2026-07-12).

## Incertidumbres explícitas

- Spec original ausente en Git.
- Trends/comparatives históricos como stubs.
- Playwright E2E NOT_VERIFIED.
