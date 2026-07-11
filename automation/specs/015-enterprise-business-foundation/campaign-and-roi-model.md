# Campaign and ROI Model — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11

---

## Ciclo

```text
objetivo → artista/lanzamiento → mercado → segmento
→ presupuesto → aprobación → ejecución → gasto
→ resultado → atribución (si aplica) → ROI o N/D → cierre → decisión
```

Prerrequisito: `rights_contract` approved para assets usados (BR-CAT-01).

---

## Entidades

campaign, campaign_budget, campaign_approval, campaign_expense, campaign_result,  
**attribution_definition**, **attributable_revenue_record**.

---

## Cálculo de ROI (estricto)

ROI solo si existen **todos**:

1. Fuente de ingreso (`attributable_revenue_record` aprobado)  
2. Moneda  
3. Periodo  
4. `attribution_definition` (versión)  
5. Versión de cálculo  
6. Nivel de confianza  
7. Responsable / aprobación del dato  

\[
ROI = \frac{\text{ingreso atribuible} - \text{gasto}}{\text{gasto}}
\]

| Condición | Resultado |
|-----------|-----------|
| gasto = 0 | **ROI = No disponible** |
| falta ingreso atribuible | **ROI = No disponible** |
| falta cualquiera de 1–7 | **ROI = No disponible** |

**Prohibido:** convertir streams u otras métricas de engagement directamente en dinero sin fuente aprobada.

---

## KPIs alternativos (cuando ROI N/D)

| Código | Nombre | Idea de fórmula |
|--------|--------|-----------------|
| KPI-CMP-02 | cost_per_result | gasto / resultados_contados |
| KPI-CMP-03 | budget_utilization | gasto / presupuesto_aprobado |
| KPI-CMP-04 | goal_attainment | resultado / objetivo |
| KPI-CMP-05 | engagement_lift | (eng_post − eng_pre) / eng_pre (si baseline existe; si no N/D) |

Ver columnas completas en `kpi-catalog.md`.

---

## Estado actual

Sin módulo campañas en código. Analytics engagement = **parcial** como insumo, no como dinero.
