> **Status:** HISTORICAL_RECONSTRUCTED
> **Original spec.md:** no disponible en Git
> **Reconstruction sources:** d2f6a27f:automation/specs/022-campaigns-budgets-and-roi/evidence/spec-closure.md; accepted-debt.md; package campaigns; docs/STATUS.md
>
> Aviso: este documento reconstruye intención histórica a partir de evidencia disponible.
> No moderniza retrospectivamente el diseño original ni afirma runtime completo.
> La verdad vigente de producto está en [`docs/STATUS.md`](../../../docs/STATUS.md).

# Spec 022 — Campaigns, Budgets and ROI

**ID:** 022
**Title:** Campaigns, Budgets and ROI
**Status:** HISTORICAL_RECONSTRUCTED

## Objetivo histórico reconstruido

Entregar gestión de campañas empresariales con presupuestos, gastos, aprobaciones, atribución y cálculo honesto de ROI, sin tratar streams como dinero.

## Actores

- Operadores de campaña (org-scoped)
- Aprobadores de campaña
- Staff con permisos `campaign.*`

## Alcance

- Tablas `app_campaign*` y relacionadas (objetivos, targets, budget, approval, expense, result, attribution, ROI snapshot, status history)
- Permisos: `campaign.view|create|update|approve|expense|close`
- ROI no disponible cuando faltan prerrequisitos

## Fuera de alcance

- Conversión FX multi-moneda
- Wizard UI completo (solo list + detail en el cierre)
- Validación cross-package de `catalog_release_id` / `artist_profile_id`
- Monetización real / pasarela de pago

## Reglas de negocio demostrables

1. ROI no se inventa cuando faltan datos previos.
2. Streams nunca se tratan como dinero.
3. Operaciones org-scoped con permisos de campaña.

## Casos de uso recuperables

1. Crear/actualizar campaña y presupuesto.
2. Registrar gastos y solicitar aprobación.
3. Cerrar campaña y consultar snapshot ROI cuando sea computable.
4. Definir atribución y resultados atribuibles.

## Criterios de aceptación verificables

- Suites históricas citadas en closure: schema/use_cases/api/security campaigns (**PASS** en el cierre 2026-07-12).
- Módulo `apps/backend/app/packages/campaigns/` presente en runtime actual.
- `docs/STATUS.md`: Campaigns/ROI = **parcial**; métricas no certificadas.

## Incertidumbres explícitas

- El `spec.md` original no está en Git; esta reconstrucción se basa en closure + debt + código.
- Playwright E2E quedó NOT_VERIFIED en el cierre.
- No se afirma certificación de ROI en el producto actual.
