# Operational Model — Procesos diarios (Spec 015)

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  

Plantilla obligatoria por proceso: actor, participantes, entrada, precondiciones, pasos numerados, reglas, estados, excepciones, aprobaciones, salida, eventos, auditoría, notificaciones, KPI, reporte, operaciones prohibidas.

Detalle de estados: `business-state-machines.md`. Reglas: `business-rules-catalog.md`.

**Caminos de adquisición:** ver § A y `commercial-model.md` — **principal = sales-assisted**; **alternativo = self-service**.

---

## A. Gestión comercial (sales-assisted)

### A. Gestión comercial — ciclo completo

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `sales_agent` (plataforma) |
| **Participantes** | `sales_manager` (aprobaciones), `platform_finance` (términos no estándar), futuro `owner` org post-conversión |
| **Entrada** | Lead inbound/outbound (email, demo, referido) |
| **Precondiciones** | Identidad de plataforma autenticada con rol sales; CRM pre-conversión es **platform-scoped** (sin `org_id`) |
| **Pasos** | 1. Crear `prospect` (`new`). 2. Registrar contacto → `contacted`. 3. Calificar → `qualified` o `disqualified`. 4. Abrir `opportunity` (`open`). 5. Elaborar `quotation` (plan, precios configurables, add-ons). 6. Enviar cotización (`sent`). 7. Negociar (descuento/términos). 8. Si umbral: solicitar aprobación. 9. Cliente acepta cotización (`accepted`). 10. Crear `commercial_contract` → aprobación/firma. 11. Conversión: provisionar `organization` + vincular `organization_id` a oportunidad/contrato. 12. Si pierde: `opportunity.lost` con razón. |
| **Reglas** | BR-COM-01…04; BR-CRM-01 (pre-conversión sin org_id) |
| **Estados** | prospect, opportunity, quotation, commercial_contract (máquinas 1–4) |
| **Excepciones** | Cotización `expired`; pérdida de oportunidad; rechazo de términos; lead duplicado |
| **Aprobaciones** | Descuento ≥ umbral (`sales_manager`); términos no estándar (`platform_finance`) |
| **Salida** | `commercial_contract.signed` + evento de conversión |
| **Eventos** | `ProspectQualified`, `OpportunityWon`, `QuotationAccepted`, `ContractAccepted`, `OrganizationProvisioned` |
| **Auditoría** | `audit_log` en cada transición; actor plataforma |
| **Notificaciones** | Cotización enviada; contrato listo; conversión a onboarding |
| **KPI** | KPI-COM-01 conversión; KPI-COM-02 pipeline; KPI-COM-03 ciclo |
| **Reporte** | Pipeline comercial |
| **Operaciones prohibidas** | Owner de org cliente operando CRM pre-conversión; convertir sin cotización aceptada (salvo excepción auditada); cotización multi-moneda |

### A-alt. Self-service (camino alternativo — no CRM completo)

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | Persona que hace signup (`identity`) |
| **Participantes** | Orquestación de aplicación; billing/subscriptions |
| **Entrada** | Signup self-service |
| **Precondiciones** | Identidad creada/verificada según política |
| **Pasos** | 1. Signup identity. 2. Crear `organization` (`provisioning`→`active`). 3. Elegir `plan`. 4. Checkout. 5. `billing_profile`. 6. `subscription` `trialing`|`active` (no existe estado `pending`). 7. Invoice/payment o trial. 8. Activation / entitlements. |
| **Reglas** | BR-ORG-*; BR-SUB-*; BR-BILL-*; sin BR-COM de pipeline |
| **Estados** | organization, subscription, invoice, payment_attempt, access |
| **Excepciones** | Pago fallido; perfil fiscal incompleto; plan no disponible |
| **Aprobaciones** | Ninguna comercial; límites del plan self-serve |
| **Salida** | Org activa + suscripción trial/active + access `full` o según trial |
| **Eventos** | `OrganizationProvisioned`, `SubscriptionActivated`, `PaymentSettled` / `PaymentAttemptFailed` |
| **Auditoría** | Sí |
| **Notificaciones** | Bienvenida; fallo de pago |
| **KPI** | KPI-PROD-01 activación; KPI-SAAS-01 MRR (si pago) |
| **Reporte** | Self-serve funnel (**futuro**) |
| **Operaciones prohibidas** | Crear prospect/opportunity como si fuera sales-assisted sin rol sales; omitir billing_profile antes de factura |

---

## B. Organización

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `administrator` / `owner` (post-conversión); en provisioning inicial: orquestación + `sales_agent` o signup |
| **Participantes** | Miembros invitados; `platform_admin` (suspensión plataforma) |
| **Entrada** | `AccountConverted` o signup self-service |
| **Precondiciones** | Contrato firmado (sales-assisted) o identity válida (self-service) |
| **Pasos** | 1. Crear `organization` (`provisioning`). 2. Asignar primer `owner`. 3. Completar datos mínimos. 4. Transición a `active`. 5. Ejecutar `onboarding_step`. 6. Emitir `invitation`. 7. Aceptación → `organization_member` + role assignment. 8. Cambios de rol (mínimo privilegio). 9. Salida de miembro (`removed`). 10. Si incidente grave: `suspended_by_platform` (no confundir con mora de suscripción). 11. Cierre `closed` con offboarding. |
| **Reglas** | BR-ORG-01…04 |
| **Estados** | organization: provisioning, active, suspended_by_platform, closed; invitation; member |
| **Excepciones** | Invite expirada; último owner no removible; intento de write en org suspendida |
| **Aprobaciones** | Transferencia de ownership; cierre de org |
| **Salida** | Org `active` con memberships gobernadas |
| **Eventos** | `OrganizationProvisioned`, `OrganizationActivated`, `MemberInvited`, `MemberJoined`, `MemberRemoved`, `OrganizationSuspendedByPlatform`, `OrganizationClosed` |
| **Auditoría** | Toda mutación de membership/rol |
| **Notificaciones** | Invite; aceptación; suspensión plataforma |
| **KPI** | KPI-ORG-01 invites aceptadas; KPI-PROD-01 activación |
| **Reporte** | Adopción por organización |
| **Operaciones prohibidas** | Cambiar estado de org por mora de pago (usar subscription/access); eliminar último owner; acceso cross-org sin justificación |

**Nota:** Mora → `subscription.past_due` + `access.limited|blocked`. La org permanece `active` salvo suspensión de plataforma o cierre.

---

## C. Suscripción

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `billing_manager` / `owner` (cambios); sistema (renovación) |
| **Participantes** | `finance`; orquestación de entitlements |
| **Entrada** | Plan seleccionado post-org |
| **Precondiciones** | Org `active` (o provisioning completo); plan publicado |
| **Pasos** | 1. Seleccionar `plan` + intervalo. 2. Opcional: iniciar `trialing`. 3. Registrar `subscription` (moneda de facturación única). 4. Materializar `subscription_entitlement` desde `plan_feature` + add-ons. 5. Add-ons → `subscription_change`. 6. Renovación: evento de ciclo → billing genera invoice. 7. Si pago OK: mantener `active` + access `full`. 8. Si fallo: `past_due` + access según política. 9. Cancelación → `canceled` (fin periodo o inmediato). 10. Sin reactivación a tiempo → `expired`. 11. Reactivación elegible crea nuevo ciclo/change auditado. |
| **Reglas** | BR-SUB-01…08 |
| **Estados** | subscription: trialing, active, past_due, canceled, expired; access: full, limited, blocked |
| **Excepciones** | Cambio de plan con prorrateo configurable; trial sin tarjeta según política |
| **Aprobaciones** | Downgrade destructivo / cancelación inmediata según política |
| **Salida** | Suscripción en estado estable + entitlements |
| **Eventos** | `SubscriptionActivated`, `SubscriptionRenewalDue`, `SubscriptionPastDue`, `SubscriptionCanceled`, `EntitlementsChanged`, `RenewalCompleted` |
| **Auditoría** | `subscription_change` + audit_log |
| **Notificaciones** | Trial ending; past_due; canceled |
| **KPI** | KPI-SAAS-01..06 |
| **Reporte** | Suscripciones / MRR |
| **Operaciones prohibidas** | subscriptions leyendo tablas internas de billing; mezclar monedas en una subscription; setear org=suspended por past_due |

---

## D. Facturación

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | Sistema billing (emisión); `finance` / `billing_manager` (ajustes) |
| **Participantes** | `platform_finance` |
| **Entrada** | Eventos de subscriptions (`SubscriptionRenewalDue`, alta, change billable) |
| **Precondiciones** | `billing_profile` completo; moneda de subscription definida |
| **Pasos** | 1. Validar/crear `billing_profile`. 2. Crear `invoice` `draft` (una moneda). 3. Añadir `invoice_item` (plan, add-ons, impuestos configurables). 4. Emitir → `issued/open`. 5. Vencimiento → `past_due` si impaga. 6. Pagos parciales vía `payment_allocation`. 7. `partially_paid` / `paid`. 8. `credit_note` / `partially_credited` / `credited`. 9. `void` solo si reglas lo permiten. |
| **Reglas** | BR-BILL-01…12 |
| **Estados** | invoice machine |
| **Excepciones** | Perfil incompleto; ítems inconsistentes; intento void tras paid |
| **Aprobaciones** | Nota de crédito sobre umbral; void |
| **Salida** | Factura emitida / cerrada / anulada |
| **Eventos** | `InvoiceIssued`, `InvoicePastDue`, `InvoicePaid`, `CreditNoteIssued`, `InvoiceVoided` |
| **Auditoría** | Emisión y correcciones; ledger no destructivo |
| **Notificaciones** | Factura emitida; recordatorio vencimiento |
| **KPI** | KPI-FIN-01 facturado; KPI-FIN-03 pendiente; KPI-FIN-04 vencido |
| **Reporte** | Cuentas por cobrar |
| **Operaciones prohibidas** | Mezclar monedas en una invoice; editar ledger destructivamente; emitir sin perfil |

---

## E. Pagos

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | Orquestación + `PaymentProvider`; `finance` (manual/transfer) |
| **Participantes** | `billing_manager`; `platform_finance` |
| **Entrada** | Invoice `issued/open` o checkout |
| **Precondiciones** | `payment_method_reference` o método manual; `idempotency_key` |
| **Pasos** | 1. Crear `payment_attempt` (`created`) con idempotency_key. 2. `PaymentProvider.create_payment` → `processing`. 3. Confirm/webhook firmado → `succeeded` o `failed`/`canceled`. 4. Si succeeded: crear/actualizar `payment` (`recorded/authorized` → `settled`). 5. `payment_allocation` a invoice(s). 6. Conciliación explícita → `reconciled`. 7. Registrar `payment_provider_event` (provider_event_id único). 8. Reintentos según política. 9. Mora: notificar → gracia (access limited) → blocked → recuperación o cancelación subscription. 10. Refund → `refund` + correcciones ledger/credit. |
| **Reglas** | BR-PAY-01…12 |
| **Estados** | payment_attempt; payment; refund; access |
| **Excepciones** | Webhook duplicado (ignorar cobro doble); firma inválida; monto/moneda mismatch |
| **Aprobaciones** | Reembolso ≥ umbral |
| **Salida** | Pago asentado/conciliado o cadena de fallo |
| **Eventos** | `PaymentAttemptFailed`, `PaymentSettled`, `PaymentReconciled`, `RefundCompleted` |
| **Auditoría** | Todos los intentos y eventos proveedor |
| **Notificaciones** | Éxito; rechazo; gracia; suspensión de acceso |
| **KPI** | KPI-FIN-02 cobrado; KPI-FIN-05 recovery; KPI-SAAS-06 delinquent |
| **Reporte** | Conciliación / mora |
| **Operaciones prohibidas** | Almacenar PAN/CVV; tratar failed attempt como payment settled; doble cobro por webhook replay |

---

## F. Gestión artística

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `artist_manager` |
| **Participantes** | `administrator`, rol `artist`, equipo |
| **Entrada** | Alta de artista en org `active` |
| **Precondiciones** | Membership activa; entitlements de roster |
| **Pasos** | 1. Crear `artist_profile` (`draft`). 2. Completar perfil. 3. `artist_assignment` a manager. 4. Activar (`active`). 5. Actualizar equipo/estado. 6. Inactivar/archivar. |
| **Reglas** | BR-ART-01…03 |
| **Estados** | artist: draft, active, inactive, archived |
| **Excepciones** | Artista sin assignment; límite de add-on artistas |
| **Aprobaciones** | Archive con derechos activos (revisión) |
| **Salida** | Artista gobernado bajo org |
| **Eventos** | `ArtistRegistered`, `ArtistAssigned`, `ArtistStatusChanged` |
| **Auditoría** | Cambios de assignment/estado |
| **Notificaciones** | Asignación a manager/artista |
| **KPI** | KPI-ART-01 artistas activos; cobertura manager |
| **Reporte** | Roster |
| **Operaciones prohibidas** | Confundir con `dim_artista` como source of truth legal; artista sin org |

---

## G. Catálogo y derechos

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `artist_manager` / administrador de derechos |
| **Participantes** | `administrator`, `auditor` |
| **Entrada** | Obra (`catalog asset`) + partes |
| **Precondiciones** | Artista/org activos |
| **Pasos** | 1. Registrar asset (ref opcional warehouse). 2. Definir `rights_type`. 3. Crear `rights_contract` + `contract_party`. 4. Set `ownership_percentage`, `territory`, `valid_from`/`valid_to`, exclusive flag, `authorized_use`. 5. Validar suma % = 100% por **asset + rights_type + territory + periodo**. 6. Aprobar (`approved`/`active`). 7. Si conflicto → `disputed` y bloquear usos. 8. Expiración/renovación contractual. |
| **Reglas** | BR-CAT-01…06 |
| **Estados** | rights_contract machine |
| **Excepciones** | Solapamiento de periodos; % ≠ 100; territorio vacío |
| **Aprobaciones** | Activación de contrato; resolución de disputa |
| **Salida** | Derechos vigentes o bloqueados |
| **Eventos** | `RightsSubmitted`, `RightsApproved`, `RightsConflictDetected`, `RightsExpired` |
| **Auditoría** | Todas las partes y % |
| **Notificaciones** | Conflicto; vencimiento próximo |
| **KPI** | KPI-CAT-01 % con derechos vigentes; conflictos abiertos |
| **Reporte** | Cobertura de derechos |
| **Operaciones prohibidas** | Campaña sobre asset disputed; validar 100% solo global sin territory/periodo |

---

## H. Campañas

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `marketing_manager` |
| **Participantes** | `owner`/`administrator` (aprobación), `analyst` |
| **Entrada** | Brief (objetivo, artista/lanzamiento, mercado, segmento) |
| **Precondiciones** | Org active; rights `approved` para assets usados; presupuesto draft |
| **Pasos** | 1. Crear `campaign` draft. 2. Definir presupuesto `campaign_budget`. 3. Solicitar `campaign_approval` si umbral. 4. Aprobar → `approved`. 5. Ejecutar `running`; registrar `campaign_expense`. 6. Capturar `campaign_result`. 7. Aplicar `attribution_definition` + `attributable_revenue_record` si hay fuente aprobada. 8. Calcular ROI solo si criterios completos; si no → “No disponible”. 9. Cerrar → decisión. |
| **Reglas** | BR-CMP-01…05; BR-CAT-01 |
| **Estados** | campaign; approval |
| **Excepciones** | Gasto > presupuesto; sin atribución; rights dispute mid-flight |
| **Aprobaciones** | Presupuesto ≥ umbral (dual) |
| **Salida** | Campaña closed + métricas / N/D |
| **Eventos** | `CampaignSubmitted`, `CampaignApproved`, `CampaignClosed`, `RoiComputed` / `RoiUnavailable` |
| **Auditoría** | Aprobaciones y gastos |
| **Notificaciones** | Pendiente aprobación; cierre |
| **KPI** | KPI-CMP-* (ROI, cost_per_result, budget_utilization, goal_attainment, engagement_lift) |
| **Reporte** | ROI / performance campaña |
| **Operaciones prohibidas** | Convertir streams en dinero sin fuente aprobada; ROI sin attribution_definition |

---

## I. Actividad y analítica

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `analyst` + ops datos |
| **Participantes** | platform ops; marketing/CS consumidores |
| **Entrada** | Eventos engagement / schedule ELT |
| **Precondiciones** | Warehouse accesible; org scope cuando aplique (**futuro**) |
| **Pasos** | 1. Ingesta. 2. Validación. 3. Transformación. 4. Publicar KPIs si freshness OK. 5. Alertas. 6. Generar insumos de reporte. 7. Apoyar `business_decision`. |
| **Reglas** | BR-AN-01…02 |
| **Estados** | executive_report; alertas operativas |
| **Excepciones** | Pipeline fail; datos stale |
| **Aprobaciones** | Publicar KPI de negocio marcado “oficial” |
| **Salida** | Métricas etiquetadas por fuente |
| **Eventos** | `PipelineSucceeded` / `PipelineFailed`, `KpiPublished`, `AnomalyDetected`, `ExecutiveReportGenerated` |
| **Auditoría** | Publicación de KPI oficiales |
| **Notificaciones** | Fallo pipeline; anomaly |
| **KPI** | KPI-DATA-01 freshness; KPI-DATA-02 pipeline success; KPIs musicales parciales |
| **Reporte** | Calidad de datos / engagement |
| **Operaciones prohibidas** | Mezclar métricas demo con MRR sin etiqueta; inventar tendencias |

---

## J. Customer Success

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `customer_success_manager` (plataforma) |
| **Participantes** | `administrator` org; support |
| **Entrada** | Nueva org / health drop / renovación próxima |
| **Precondiciones** | Org active; snapshots habilitados |
| **Pasos** | 1. Guiar `onboarding_step`. 2. Medir adopción. 3. Calcular `customer_health_snapshot`. 4. Si risk/critical → intervención. 5. Coordinar renovación/expansión. 6. Hand-off a sales si upsell. |
| **Reglas** | BR-CS-01…02 |
| **Estados** | health score machine |
| **Excepciones** | Datos usage incompletos → health “watch” |
| **Aprobaciones** | Crédito comercial excepcional (con finance) |
| **Salida** | Intervención registrada / renovación |
| **Eventos** | `OnboardingCompleted`, `HealthChanged`, `InterventionOpened` |
| **Auditoría** | Intervenciones y accesos CS |
| **Notificaciones** | Risk alert a CSM |
| **KPI** | KPI-CS-* |
| **Reporte** | Health portfolio |
| **Operaciones prohibidas** | CSM sin justificación en datos de otra org no asignada |

---

## K. Soporte

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `support_agent` |
| **Participantes** | `platform_admin`, `security_admin`, `platform_finance` |
| **Entrada** | Ticket de usuario/org |
| **Precondiciones** | Identidad; org context si aplica |
| **Pasos** | 1. Crear `support_case`. 2. Clasificar/priorizar. 3. Asignar. 4. Responder (`support_message`). 5. Escalar (billing/security/tech). 6. Resolver. 7. Cerrar + CSAT opcional. |
| **Reglas** | BR-SUP-01…02 |
| **Estados** | ticket machine |
| **Excepciones** | Reopen; PII breach sospechado |
| **Aprobaciones** | Escalamiento security |
| **Salida** | Caso cerrado |
| **Eventos** | `TicketCreated`, `TicketEscalated`, `TicketClosed` |
| **Auditoría** | Acceso a datos org durante ticket |
| **Notificaciones** | Updates al solicitante |
| **KPI** | KPI-SUP-01 TTR; KPI-SUP-02 CSAT |
| **Reporte** | Backlog soporte |
| **Operaciones prohibidas** | Refund desde soporte sin finance; acceso cross-org permanente |

---

## L. Seguridad y cumplimiento

| Campo | Contenido |
|-------|-----------|
| **Actor responsable** | `security_admin` |
| **Participantes** | `auditor`, `platform_admin`, DPO-like rol futuro |
| **Entrada** | Consentimiento, incidente, DSR, acceso sensible |
| **Precondiciones** | Políticas de retención configurables definidas (diseño) |
| **Pasos** | 1. Registrar `consent_record` / aceptación términos. 2. Controlar acceso sensible (justificación + audit). 3. Abrir incidente. 4. Contener/erradicar/recuperar. 5. Atender solicitud de datos/eliminación según retención. 6. Retener evidencias. 7. Cerrar con lecciones. |
| **Reglas** | BR-CMPL-01…03 |
| **Estados** | incident (vía approval/ticket patterns); consent activo/revocado |
| **Excepciones** | Retención legal vs borrado; conflicto de obligaciones (**diseñado**, no jurisdicción afirmada) |
| **Aprobaciones** | Borrado irreversible; disclosure |
| **Salida** | Registro de cumplimiento / incidente cerrado |
| **Eventos** | `ConsentRecorded`, `IncidentOpened`, `DsrCompleted` |
| **Auditoría** | Obligatoria e inmutable lógicamente |
| **Notificaciones** | A afectados según política diseñada (no afirmada legalmente) |
| **KPI** | KPI-SEC-01 audited access; KPI-SEC-02 MTTR |
| **Reporte** | Auditoría / incidentes |
| **Operaciones prohibidas** | Afirmar certificación GDPR/PCI/ISO; acceso cross-org sin audit |

---

## Matriz proceso → dominio

| Proceso | Dominios |
|---------|----------|
| A | crm, contracts (+ orquestación orgs) |
| A-alt | identity, organizations, subscriptions, billing |
| B | organizations, identity |
| C | subscriptions |
| D–E | billing (consume events subscriptions) |
| F | artists |
| G | catalog_rights |
| H | campaigns |
| I | engagement, analytics, reporting |
| J | customer_success |
| K | support |
| L | compliance, platform |
