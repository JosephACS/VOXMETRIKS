# Operativo · Táctico · Estratégico

Este documento recupera los ocho objetivos diseñados en la Spec 015 y los contrasta con el runtime vigente. No define metas numéricas ni confunde datos demo con resultados reales.

## Cadena canónica

```text
negocio → objetivo estratégico → KPI/fuente → reporte o recomendación explicable
→ decisión humana → aprobar/cancelar → acción → seguimiento → resultado
```

La trazabilidad de producto se diseña con Specs. Airflow coordina el ELT analítico; no coordina los procesos humanos ni reemplaza la decisión empresarial.

## Estratégico — ocho objetivos vigentes

| Código | Objetivo | Evidencia disponible | Madurez honesta |
|--------|----------|----------------------|------------------|
| OE-01 | Aumentar organizaciones activas | Organizaciones, membresías y suscripciones | Fuente implementada; KPI estratégico por periodo pendiente |
| OE-02 | Generar ingresos recurrentes | `active_mrr`, `active_arr`, planes y precios | KPI implementado por organización; sin FX ni ingreso reconocido |
| OE-03 | Mejorar renovación | Cambios/cancelaciones de suscripción y riesgos CS | Parcial; `renewal_rate` y churn estratégico pendientes |
| OE-04 | Demostrar valor mediante ROI | Campañas, presupuesto y snapshots ROI | Parcial/simulado; ROI no certificado |
| OE-05 | Aumentar adopción | Onboarding, invitaciones, membresías y uso | Fuentes parciales; definición final de activación pendiente |
| OE-06 | Garantizar calidad de datos | Airflow, `ctl_*`, validación y calidad KPI | Orquestación verificada; rollup estratégico pendiente |
| OE-07 | Proteger información empresarial | RBAC org, auditoría, sesiones e incidentes | Implementado/parcial; KPI de cobertura pendiente |
| OE-08 | Mantener sostenibilidad operativa | Health, Workpanel, jobs e incidentes | Operación implementada; soporte/SLA final diferido |

Las metas comerciales siguen diferidas hasta que producto apruebe baseline, ventana y fuente. “No disponible” es preferible a un valor inventado.

## Táctico

Áreas: Dirección, Comercial/CRM, Suscripciones, Billing, Artistas/Catálogo, Marketing/Campañas, Analítica/Reportes y Ops/Compliance.

- Reportes complejos y business analytics resumen tendencias y excepciones.
- Las recomendaciones empresariales actuales son **reglas explicables** y se registran con `is_ai=false`.
- Los reportes ejecutivos congelan evidencia y permiten convertirla en decisiones controladas.

Varias áreas tienen APIs/UI **implementadas** o **parciales**; ver [`../STATUS.md`](../STATUS.md).

## Operativo

Casos de uso diarios en SPA/API: login, espacios, escucha, administración de organización, billing, artistas, catálogo, campañas, reportes, decisiones, acciones y seguimiento.

El Workpanel y los reportes simples muestran pendientes operativos. La base `app_*` y el warehouse analítico comparten DuckDB por alcance académico; no se presentan como dos bases productivas independientes.

## Datos e IA

- Carril analítico: PocketBase/Parquet → Airflow → Bronze/Silver/Gold → `dim_*`/`fact_*`/`agg_*` → KPI/reporte.
- Carril transaccional: UI/API → CRUD `app_*` → estados/auditoría.
- Parte de la actividad del warehouse es sintética o proxy; debe conservar su clasificación al publicar KPIs.
- La IA musical usa ranking heurístico, coescucha y similitud; no es un modelo estratégico predictivo.
- La revisión de IA para dashboards estratégicos se realizará después del cierre Operativo/Táctico/Estratégico AGG, no dentro de esta consolidación.
