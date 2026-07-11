# Domain Boundaries — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  

**Regla de oro:** cada entidad tiene **un solo dominio propietario**.  
**Sin dependencia circular** subscriptions ↔ billing.

Flujo:

```text
subscriptions publica Subscription* / Entitlements* / Usage*
  → billing consume y emite Invoice* / Payment*
  → billing publica PaymentSettled / PaymentAttemptFailed
  → capa de aplicación/orquestación actualiza access/entitlements
subscriptions NO consulta tablas internas de billing
```

Ver catálogo canónico de eventos en `business-state-machines.md`.

CRM pre-conversión: **platform-scoped** (sin `org_id`). Post-conversión: vínculo a `organization_id`.

---

## identity

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Personas, credenciales, sesiones, autenticación |
| **Entidades** | user, session, credential (hash), (catálogo global de permission codes si aplica) |
| **Procesos** | Signup, login, verify, logout, reset |
| **Datos propietarios** | identidad personal, secretos de auth |
| **Eventos publicados** | UserRegistered, UserAuthenticated, UserDisabled |
| **Eventos consumidos** | — |
| **Deps permitidas** | — |
| **Deps prohibidas** | billing, campaigns, catalog_rights |
| **APIs futuras** | `/api/v1/identity/*` (evolucionar actual) |
| **UI futura** | login, registro, perfil persona |
| **Reportes** | accesos fallidos (ops) |
| **Estado actual** | **Parcial/implementado** (`packages/identity`) |

## organizations

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Tenancy B2B, membresías, invitaciones, role assignments org |
| **Entidades** | organization, organization_member, invitation, business_role assignment |
| **Procesos** | B |
| **Datos propietarios** | org profile, memberships |
| **Publica** | OrganizationProvisioned, OrganizationActivated, Member*, OrganizationSuspendedByPlatform, OrganizationClosed |
| **Consume** | UserAuthenticated (identity); ContractAccepted / conversion signal (contracts/crm) |
| **Deps OK** | identity |
| **Deps NO** | billing internals; campaigns write |
| **APIs** | `/organizations/*`, `/invitations/*` |
| **UI** | settings org, members |
| **Reportes** | adopción membresías |
| **Estado** | **Diseñado** |

## crm

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Pipeline pre y peri-conversión operado por personal plataforma |
| **Entidades** | prospect, opportunity, quotation |
| **Procesos** | A sales-assisted |
| **Datos** | leads platform-scoped |
| **Publica** | Prospect*, Opportunity*, Quotation*, AccountConverted (señal) |
| **Consume** | plan catalog (subscriptions read) |
| **Deps OK** | identity (sales users); subscriptions **read** plans |
| **Deps NO** | organizations write pre-conversión; billing write |
| **APIs** | `/crm/*` |
| **UI** | pipeline interno VOXMETRIKS |
| **Reportes** | pipeline |
| **Estado** | **Diseñado** |
| **Scope** | Sin `org_id` hasta conversión; luego `organization_id` opcional/requerido post |

## contracts

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Contratos comerciales B2B |
| **Entidades** | commercial_contract |
| **Procesos** | A (cierre) |
| **Datos** | términos firmados |
| **Publica** | ContractAccepted, ContractActivated, ContractTerminated |
| **Consume** | QuotationAccepted; OrganizationProvisioned |
| **Deps OK** | crm, organizations (post), identity |
| **Deps NO** | payment provider directo |
| **APIs** | `/contracts/*` |
| **UI** | contratos internos |
| **Reportes** | win contracts |
| **Estado** | **Diseñado** |

## subscriptions

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Planes, suscripciones, entitlements, usage |
| **Entidades** | plan, plan_price, plan_feature, addon, subscription, subscription_change, subscription_entitlement, usage_record |
| **Procesos** | C |
| **Datos** | ciclo de vida sub + moneda de facturación de la sub |
| **Publica** | SubscriptionActivated, SubscriptionRenewalDue, SubscriptionPastDue, SubscriptionCanceled, EntitlementsChanged, UsageRecorded, RenewalCompleted |
| **Consume** | OrganizationActivated; PaymentSettled / PaymentAttemptFailed (**eventos**, no tablas billing); orquestación access |
| **Deps OK** | organizations; identity |
| **Deps NO** | **consultar tablas invoice/payment**; catalog_rights |
| **APIs** | `/plans/*`, `/subscriptions/*` |
| **UI** | plan picker, subscription settings |
| **Reportes** | MRR (vía reporting que agrega) |
| **Estado** | **Diseñado** |

## billing

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Perfil fiscal, facturas, intentos, pagos, allocations, refunds, credit notes, ledger, provider events |
| **Entidades** | billing_profile, invoice, invoice_item, payment_method_reference, payment_attempt, payment, payment_allocation, refund, credit_note, payment_provider_event, billing_ledger_entry |
| **Procesos** | D, E |
| **Datos** | documentos financieros y conciliación |
| **Publica** | InvoiceIssued, InvoicePastDue, InvoicePaid, PaymentSettled, PaymentAttemptFailed, PaymentReconciled, RefundCompleted, CreditNoteIssued |
| **Consume** | SubscriptionRenewalDue, SubscriptionActivated, EntitlementsChanged (billable), Organization* (profile) |
| **Deps OK** | organizations (profile); subscriptions **solo vía eventos** |
| **Deps NO** | mutar subscription rows directamente (orquestación); artists |
| **APIs** | `/billing/*`, `/invoices/*`, `/payments/*` |
| **UI** | facturación, métodos de pago (token) |
| **Reportes** | AR, cobrado, mora |
| **Estado** | **Diseñado** |

## artists

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Perfiles y assignments artísticos de negocio |
| **Entidades** | artist_profile, artist_assignment |
| **Procesos** | F |
| **Publica** | ArtistRegistered, ArtistAssigned, ArtistStatusChanged |
| **Consume** | OrgActivated |
| **Deps OK** | organizations |
| **Deps NO** | billing; confundir con dim_artista como owner |
| **APIs** | `/artists/*` |
| **UI** | roster |
| **Reportes** | roster |
| **Estado** | **Diseñado** |

## catalog_rights

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Ownership y contratos de derechos por asset/tipo/territorio/periodo |
| **Entidades** | catalog_ownership (asset link), rights_contract, contract_party, territory |
| **Procesos** | G |
| **Publica** | RightsApproved, RightsConflictDetected, RightsExpired |
| **Consume** | Artist* |
| **Deps OK** | artists, organizations |
| **Deps NO** | billing; campaigns write |
| **APIs** | `/catalog-rights/*` |
| **UI** | derechos |
| **Reportes** | cobertura derechos |
| **Estado** | **Diseñado** |

## campaigns

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Campañas, presupuestos, aprobaciones, gastos, resultados, atribución |
| **Entidades** | campaign, campaign_budget, campaign_approval, campaign_expense, campaign_result, attribution_definition, attributable_revenue_record |
| **Procesos** | H |
| **Publica** | CampaignSubmitted, CampaignApproved, CampaignClosed, RoiComputed, RoiUnavailable |
| **Consume** | RightsApproved; analytics read; Org* |
| **Deps OK** | organizations, artists, catalog_rights (read), analytics (read) |
| **Deps NO** | emitir invoices; inventar revenue |
| **APIs** | `/campaigns/*` |
| **UI** | campañas |
| **Reportes** | ROI / performance |
| **Estado** | **Diseñado** |

## engagement

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Eventos de uso/listening |
| **Entidades** | (hechos/eventos; hoy warehouse/app) |
| **Procesos** | I (entrada) |
| **Publica** | EngagementObserved |
| **Consume** | — |
| **Deps OK** | identity (actor), organizations (**futuro** scope) |
| **Deps NO** | PAN; rights mutates |
| **APIs** | events ingest |
| **UI** | player/exploración (**parcial**) |
| **Reportes** | engagement |
| **Estado** | **Parcial** |

## analytics

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Agregaciones y KPIs de comportamiento/catálogo |
| **Entidades** | aggregates / views conceptuales |
| **Procesos** | I |
| **Publica** | KpiPublished (engagement) |
| **Consume** | engagement |
| **Deps OK** | engagement |
| **Deps NO** | ownership legal; billing ledger |
| **APIs** | `/analytics/*` (**parcial** hoy) |
| **UI** | dashboards (**parcial**) |
| **Reportes** | musicales |
| **Estado** | **Parcial** |

## reporting

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Reportes ejecutivos y decisiones |
| **Entidades** | executive_report, business_decision |
| **Procesos** | I (salida), dirección |
| **Publica** | ExecutiveReportGenerated, BusinessDecisionRecorded |
| **Consume** | analytics, billing aggregates (event/API), campaigns |
| **Deps OK** | analytics, campaigns, billing **read aggregates**, subscriptions read |
| **Deps NO** | mutar payments |
| **APIs** | `/reporting/*` |
| **UI** | executive |
| **Reportes** | board pack |
| **Estado** | **Diseñado** (dashboards actuales ≠ este dominio) |

## customer_success

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Onboarding, health, intervenciones |
| **Entidades** | onboarding_step, customer_health_snapshot |
| **Procesos** | J |
| **Publica** | HealthChanged, OnboardingCompleted |
| **Consume** | Org*, Subscription*, usage signals, Ticket* |
| **Deps OK** | organizations, subscriptions (events), support read |
| **Deps NO** | refunds |
| **APIs** | `/customer-success/*` |
| **UI** | CS console interna |
| **Reportes** | health portfolio |
| **Estado** | **Diseñado** |

## support

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Tickets y mensajes |
| **Entidades** | support_case, support_message |
| **Procesos** | K |
| **Publica** | Ticket* |
| **Consume** | identity, organizations |
| **Deps OK** | identity, organizations |
| **Deps NO** | emitir credit notes |
| **APIs** | `/support/*` |
| **UI** | helpdesk |
| **Reportes** | backlog |
| **Estado** | **Diseñado** |

## compliance

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Consentimiento, DSR, retención, auditoría de negocio |
| **Entidades** | consent_record, audit_log (política), (incident records conceptuales) |
| **Procesos** | L |
| **Publica** | Consent*, Dsr*, Incident* |
| **Consume** | cross-domain read con control |
| **Deps OK** | identity, organizations (scope) |
| **Deps NO** | reescribir ledger billing |
| **APIs** | `/compliance/*` |
| **UI** | privacy center |
| **Reportes** | audit |
| **Estado** | **Diseñado** |

## platform

| Campo | Contenido |
|-------|-----------|
| **Responsabilidad** | Ops, providers config, webhooks infra, feature flags |
| **Entidades** | business_event (bus), notification, provider configs |
| **Procesos** | transversal |
| **Publica** | ProviderConfigured, NotificationSent |
| **Consume** | health signals |
| **Deps OK** | todos (infra) sin poseer datos de negocio ajenos |
| **Deps NO** | poseer invoice como source of truth |
| **APIs** | `/platform/*`, webhooks |
| **UI** | admin plataforma |
| **Reportes** | availability |
| **Estado** | **Parcial** |

---

## Diagrama de dependencias (sin ciclos)

```text
identity
  └─ organizations
       ├─ crm (sales users) ── contracts ──► organizations (convert)
       ├─ subscriptions ──events──► billing ──events──► orchestration ──► subscriptions/access
       ├─ artists ──► catalog_rights ──► campaigns
       ├─ customer_success / support
       └─ compliance
engagement ──► analytics ──► reporting
platform (transversal)
```
