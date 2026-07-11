# KPI Catalog — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  
**Sin series ni metas reales inventadas.** Metas estratégicas siguen siendo **propuestas** en strategic-model.

Columnas obligatorias: código · nombre · fórmula · fuente · granularidad · frecuencia · propietario · limitaciones · nulos/denominador cero · madurez.

---

## Comerciales

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-COM-01 | conversion_rate | won / (won+lost) | crm | pipeline | M | sales_manager | sin CRM = N/D | si closed=0 → N/D | Propuesto |
| KPI-COM-02 | pipeline_value | Σ amount open+negotiation | crm | moneda | M | sales_manager | estimates | null amount excluir o N/D política | Propuesto |
| KPI-COM-03 | sales_cycle_days | won_at − created_at (avg) | crm | opp | M | sales_manager | solo won | sin fechas → excluir | Propuesto |
| KPI-COM-04 | won_opps | count won | crm | count | M | sales_agent | — | 0 válido | Propuesto |
| KPI-COM-05 | lost_opps | count lost | crm | count | M | sales_agent | — | 0 válido | Propuesto |

## SaaS

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-SAAS-01 | gross_mrr | Σ mensualizado subscriptions active+past_due (política) antes de créditos | subscriptions+prices | plataforma/org | M | finance | precios config | sin price → excluir línea | Propuesto |
| KPI-SAAS-02 | net_mrr | gross_mrr − credits/refunds reconocidos en periodo (si se modelan) | subscriptions+billing events | plataforma/org | M | finance | depende eventos billing | si gross null → N/D | Propuesto |
| KPI-SAAS-03 | arr | net_mrr × 12 (o gross×12 si net N/D — etiquetar) | derivado | plataforma | M | finance | simplificación | N/D si mrr N/D | Propuesto |
| KPI-SAAS-04 | logo_churn | orgs canceled/expired / orgs inicio | subscriptions | logo | M | CS | ≠ revenue churn | inicio=0 → N/D | Propuesto |
| KPI-SAAS-05 | revenue_churn | MRR perdido / MRR inicio | subscriptions | revenue | M | finance | definir lost MRR | inicio=0 → N/D | Propuesto |
| KPI-SAAS-06 | renewal_rate | renovadas / elegibles | subscriptions | cohorte | M | CS | definir elegibles | elegibles=0 → N/D | Propuesto |
| KPI-SAAS-07 | expansion_mrr | net upsell/addons | subscriptions | org | M | CS/sales | — | 0 válido | Propuesto |
| KPI-SAAS-08 | arpa | net_mrr / paying_orgs | derivado | plataforma | M | finance | — | paying=0 → N/D | Propuesto |
| KPI-SAAS-09 | accounts_delinquent | count past_due/grace/blocked access | subscriptions+access | org | W/M | finance | — | 0 válido | Propuesto |

## Financieros

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-FIN-01 | invoiced_amount | Σ invoices issued (no void) | billing | moneda | M | finance | no FX v1 | 0 válido | Propuesto |
| KPI-FIN-02 | collected_amount | Σ payments settled/reconciled | billing | moneda | M | finance | ≠ ingreso reconocido | 0 válido | Propuesto |
| KPI-FIN-03 | outstanding | issued − allocated − credited | billing | moneda | M | finance | — | 0 válido | Propuesto |
| KPI-FIN-04 | overdue_amount | outstanding where past_due | billing | moneda | M | finance | — | 0 válido | Propuesto |
| KPI-FIN-05 | recovery_rate | recovered / entered_collections | billing | cohorte | M | finance | definir collections | denom 0 → N/D | Propuesto |
| KPI-FIN-06 | refunds_amount | Σ refunds completed | billing | moneda | M | finance | — | 0 válido | Propuesto |
| KPI-FIN-07 | recognized_revenue | — | — | — | — | — | **Fuera de alcance v1** (no ASC/IFRS diseñado) | N/A | Fuera de alcance |

## Producto / adopción

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-PROD-01 | activation_rate | orgs onboarding_core done / orgs nuevas | CS | cohorte | S/M | CSM | definir core | nuevas=0 → N/D | Propuesto |
| KPI-PROD-02 | adoption_rate | features_used / features_entitled | entitlements+usage | org | M | CSM | — | entitled=0 → N/D | Propuesto |
| KPI-PROD-03 | active_members | members con actividad en ventana | usage/events | org | W | analyst | hoy users app ≠ org | sin org scope → Parcial | Parcial/Propuesto |
| KPI-PROD-04 | time_to_first_value | first meaningful − start | events | org | M | CSM | definir meaningful | sin evento → N/D | Propuesto |

## Customer Success / Soporte

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-CS-01 | health_distribution | count by health state | CS snapshots | org | W | CSM | componentes config | sin snapshot → N/D | Propuesto |
| KPI-CS-02 | at_risk_accounts | count risk+critical | CS | org | W | CSM | — | 0 válido | Propuesto |
| KPI-CS-03 | onboarding_completed_pct | done / started | onboarding_step | cohorte | M | CSM | — | started=0 → N/D | Propuesto |
| KPI-CS-04 | renewals_saved | interventions → renewed | CS+subs | count | M | CSM | atribución débil | 0 válido | Propuesto |
| KPI-SUP-01 | time_to_resolution | resolved_at − created_at | support | ticket | W | support | — | sin resolve excluir | Propuesto |
| KPI-SUP-02 | csat | avg score | support | ticket | M | support | opcional | sin respuestas → N/D | Propuesto |

## Datos / seguridad

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-DATA-01 | kpi_freshness | now − last_success_load | warehouse ctl | sistema | D | datos | no es KPI SaaS | sin load → N/D | Actual/parcial |
| KPI-DATA-02 | pipeline_success_rate | successes / runs | ELT | sistema | D | ops | — | runs=0 → N/D | Actual/parcial |
| KPI-SEC-01 | sensitive_access_audited_pct | audited / sensitive_accesses | compliance | sistema | M | security | RBAC org futuro | denom 0 → N/D | Propuesto |
| KPI-SEC-02 | incident_mttr | resolve − detect | compliance | incident | M | security | — | sin resolve excluir | Propuesto |

## Musicales / engagement

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-MUS-01 | streams | count streams | warehouse/app | track/artist | D/W | analyst | puede ser demo/sintético | 0 válido | Actual/parcial |
| KPI-MUS-02 | listeners | distinct listeners | warehouse | artist/market | W | analyst | definición listener | 0 válido | Parcial |
| KPI-MUS-03 | searches | count searches | app | — | W | analyst | — | 0 válido | Parcial |
| KPI-MUS-04 | favorites | count favorites | app | — | W | analyst | — | 0 válido | Parcial |
| KPI-MUS-05 | skips | count skips | events | — | W | analyst | — | 0 válido | Parcial/Propuesto |
| KPI-MUS-06 | engagement_score_proxy | fórmula producto actual si existe | analytics | track | W | analyst | etiquetar fuente | null → “No disponible” | Parcial |
| KPI-MUS-07 | growth_rate | (v_t − v_t-1)/v_t-1 | analytics | artist/track | M | analyst | — | v_t-1=0 → N/D | Parcial |

## Campañas

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-CMP-01 | campaign_roi | (attr_rev − spend)/spend | campaigns+attr | campaña | cierre | marketing | requiere 7 condiciones | spend=0 o sin attr → **No disponible** | Propuesto |
| KPI-CMP-02 | cost_per_result | spend / results | campaigns | campaña | cierre | marketing | definir result | results=0 → N/D | Propuesto |
| KPI-CMP-03 | budget_utilization | spend / approved_budget | campaigns | campaña | W/cierre | marketing | — | budget=0 → N/D | Propuesto |
| KPI-CMP-04 | goal_attainment | result / goal | campaigns | campaña | cierre | marketing | — | goal=0 → N/D | Propuesto |
| KPI-CMP-05 | engagement_lift | (eng_post − eng_pre)/eng_pre | analytics+campaign | campaña | cierre | analyst | baseline required | eng_pre=0 → N/D | Propuesto |

## Organizaciones

| código | nombre | fórmula | fuente | granularidad | frecuencia | propietario | limitaciones | nulos/denominador 0 | madurez |
|--------|--------|---------|--------|--------------|------------|-------------|--------------|---------------------|---------|
| KPI-ORG-01 | invite_accept_rate | accepted / sent | organizations | org | M | admin | — | sent=0 → N/D | Propuesto |
| KPI-ORG-02 | orgs_active | count org active con sub usable | orgs+subs | plataforma | M | dirección | definir usable | 0 válido | Propuesto |

## Regla de publicación

Si falta fuente, freshness o denom=0 según tabla → **No disponible**, no inventar.
