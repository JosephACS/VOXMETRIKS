# Tactical Model — Áreas empresariales (Spec 015)

**Status**: Diseñado  
**Fecha**: 2026-07-11

Para cada área: responsabilidad, objetivos tácticos, procesos, roles, info consumida/producida, KPIs, decisiones.

---

## 1. Dirección

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Estrategia, prioridades, decisiones de inversión y riesgo |
| **Objetivos tácticos** | OT-DIR-01 Alinear portfolio a OE-01…08; OT-DIR-02 Aprobar excepciones de alto impacto |
| **Procesos** | Revisión ejecutiva; aprobación de campañas grandes; go/no-go renovación estratégica |
| **Roles** | owner (org); platform_admin (plataforma) |
| **Consume** | Executive reports, KPIs, health, pipeline comercial |
| **Produce** | `business_decision`, prioridades, excepciones |
| **KPIs** | ROI portfolio, orgs_active, MRR, churn |
| **Decisiones** | Expandir/contratar; congelar features; aceptar deuda |

---

## 2. Comercial

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Pipeline, cotizaciones, contratos, conversión |
| **Objetivos** | OT-COM-01 Generar oportunidades calificadas; OT-COM-02 Convertir a suscripción |
| **Procesos** | A (gestión comercial) completo |
| **Roles** | owner, administrator; (futuro: sales — mapeado a admin/owner si no existe rol dedicado) |
| **Consume** | Prospectos, planes, precios configurables |
| **Produce** | opportunity, quotation, commercial_contract |
| **KPIs** | Conversión, pipeline value, win/loss |
| **Decisiones** | Descuento; priorizar cuenta; perder oportunidad |

---

## 3. Marketing

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Campañas, segmentos, gasto, atribución |
| **Objetivos** | OT-MKT-01 Ejecutar campañas con ROI medible |
| **Procesos** | H (campañas) |
| **Roles** | marketing_manager, analyst |
| **Consume** | Artistas, catálogo, presupuestos, analytics |
| **Produce** | campaign_*, resultados, aprendizajes |
| **KPIs** | ROI, gasto vs presupuesto, conversiones atribuidas |
| **Decisiones** | Pausar/escalar campaña; reasignar presupuesto |

---

## 4. Finanzas

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Facturación, cobranza, conciliación, mora |
| **Objetivos** | OT-FIN-01 Cobrar a tiempo; OT-FIN-02 Reducir vencido |
| **Procesos** | D (facturación), E (pagos) |
| **Roles** | billing_manager, finance, platform_finance |
| **Consume** | subscriptions, billing_profile, payment webhooks |
| **Produce** | invoice, payment, refund, credit_note |
| **KPIs** | Facturado, cobrado, vencido, recovery rate |
| **Decisiones** | Nota de crédito; plan de pagos; suspensión por mora |

---

## 5. Customer Success

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Onboarding, adopción, health, renovación, expansión |
| **Objetivos** | OT-CS-01 Completar onboarding; OT-CS-02 Mitigar churn |
| **Procesos** | J (CS) |
| **Roles** | administrator, support_agent (plataforma), CS como función |
| **Consume** | usage, health snapshots, tickets |
| **Produce** | intervenciones, planes de adopción |
| **KPIs** | Health, onboarding %, renovaciones |
| **Decisiones** | Intervenir; proponer upsell; escalar a soporte |

---

## 6. Soporte

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Tickets, SLA, escalamiento, CSAT |
| **Objetivos** | OT-SUP-01 Resolver en SLA; OT-SUP-02 Reducir backlog |
| **Procesos** | K (soporte) |
| **Roles** | support_agent, platform_admin |
| **Consume** | Casos, logs, contexto org |
| **Produce** | resoluciones, knowledge |
| **KPIs** | Tiempo resolución, CSAT, reopen rate |
| **Decisiones** | Prioridad; escalar seguridad/finanzas |

---

## 7. Gestión artística

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Roster, managers, perfiles, estados de artista |
| **Objetivos** | OT-ART-01 Mantener roster gobernado |
| **Procesos** | F (gestión artística) |
| **Roles** | artist_manager, artist, administrator |
| **Consume** | Org membership, assignments |
| **Produce** | artist_profile, artist_assignment |
| **KPIs** | Artistas activos, cobertura de manager |
| **Decisiones** | Alta/baja artista; reasignar manager |

---

## 8. Catálogo y derechos

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Álbumes, canciones, ownership, contratos, territorios |
| **Objetivos** | OT-CAT-01 Derechos claros antes de monetizar campañas |
| **Procesos** | G (catálogo y derechos) |
| **Roles** | artist_manager, administrator, auditor |
| **Consume** | Contratos, partes, % |
| **Produce** | rights_contract, catalog_ownership, conflictos |
| **KPIs** | % catálogo con derechos vigentes; conflictos abiertos |
| **Decisiones** | Aprobar contrato; bloquear uso en campaña |

**Nota:** Distinto del catálogo warehouse (`dim_track`) — ver contradicciones.

---

## 9. Datos y analítica

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Ingesta, calidad, KPIs, alertas, apoyo a decisiones |
| **Objetivos** | OT-DAT-01 Publicar KPIs confiables; OT-DAT-02 Detectar anomalías |
| **Procesos** | I (actividad y analítica) |
| **Roles** | analyst; ops plataforma |
| **Consume** | Engagement, warehouse, business_events |
| **Produce** | métricas, alertas, datasets de reporte |
| **KPIs** | Freshness, pipeline success, uso de dashboards |
| **Decisiones** | Invalidar métrica; priorizar fix de datos |

---

## 10. Seguridad y cumplimiento

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Consentimiento, accesos, incidentes, retención, auditoría |
| **Objetivos** | OT-SEC-01 Auditar sensible; OT-SEC-02 Responder incidentes |
| **Procesos** | L (seguridad y cumplimiento) |
| **Roles** | security_admin, auditor, platform_admin |
| **Consume** | access logs, consent_record |
| **Produce** | incidentes, evidencias, políticas aplicadas |
| **KPIs** | Cobertura auditoría, MTTR |
| **Decisiones** | Revocar acceso; retener/borrar |

---

## 11. Operaciones de plataforma

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Disponibilidad, integraciones, ELT, feature flags operativos |
| **Objetivos** | OT-OPS-01 Disponibilidad; OT-OPS-02 Activación técnica; OT-OPS-03 Pipelines sanos |
| **Procesos** | Health, deploy, validación warehouse (hoy **parcial**) |
| **Roles** | platform_admin |
| **Consume** | Health, CI, logs |
| **Produce** | Estado de plataforma, cambios operativos |
| **KPIs** | Availability, job success |
| **Decisiones** | Mantener/modo degradado; habilitar provider mock |

---

## 12. Administración

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Membresías, roles, configuración org, planes visibles |
| **Objetivos** | OT-ADM-01 Gobernar membresías; OT-ADM-02 Permisos mínimos; OT-ADM-03 Configuración comercial org |
| **Procesos** | B (organización), C (suscripción) parcial admin |
| **Roles** | owner, administrator |
| **Consume** | Invitations, roles |
| **Produce** | membership changes, config |
| **KPIs** | Invites aceptadas, miembros activos |
| **Decisiones** | Suspender miembro; cambiar rol |
