# Closure — 022 Campaigns, Budgets and ROI

**Status:** HISTORICAL_RECONSTRUCTED / CLOSED_WITH_ACCEPTED_DEBT (evidence @ d2f6a27f)
**Date (histórico):** 2026-07-12

## Resultado actual (`docs/STATUS.md`)

Campaigns / ROI: **parcial** — módulo presente; métricas no certificadas.

## Recuperado

- Dominio campaigns con tablas y permisos descritos en evidence de cierre.
- Paquete backend campaigns y tests L4 de servicio en frontend.

## Reemplazado

- N/A a nivel de ID; consolidaciones posteriores no renumeran 022.

## Excluido o diferido

- Playwright E2E NOT_VERIFIED
- FX multi-currency
- Campaign wizard UI
- Cross-package ID validation

## Evidencia (código/pruebas)

- `apps/backend/app/packages/campaigns/`
- `apps/backend/tests/test_campaigns_schema_o1.py`
- `apps/backend/tests/test_campaigns_use_cases_o2.py`
- `apps/backend/tests/test_campaigns_api_o3.py`
- `apps/backend/tests/test_campaigns_security_o5.py`
- `apps/frontend/src/app/packages/campaigns/services/campaigns-l4.spec.ts`
- Evidence histórica: `d2f6a27f:automation/specs/022-.../evidence/`

## Commits relevantes

- Evidence preservada en `d2f6a27f` bajo `automation/specs/022-.../evidence/`
- Consolidación documental `2c8d489b`

## Deuda restante

Ver accepted-debt histórico + STATUS: ROI no certificado; E2E no verificado.

## Nivel de confianza

**Medio-alto** para alcance de tablas/permisos (closure contemporáneo). **Medio** para equivalencia exacta del spec original (ausente).
