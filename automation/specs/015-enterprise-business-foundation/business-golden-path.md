# Business Golden Path — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  

**Camino principal:** sales-assisted (pasos 1–22 abajo).  
**Camino alternativo:** self-service (sección variantes).

Plantilla por paso: actor · entrada · regla · estado · dato · evento · pantalla futura · endpoint futuro · prueba futura · KPI · excepción principal.

---

## Camino principal (sales-assisted)

### Paso 1 — Prospecto
| Campo | Valor |
|-------|-------|
| Actor | sales_agent |
| Entrada | Lead |
| Regla | BR-CRM-01/02 |
| Estado | prospect new→… |
| Dato | prospect |
| Evento | Prospect* |
| Pantalla | CRM → Prospects |
| Endpoint | `POST /api/v1/crm/prospects` |
| Prueba | crear/contact/qualify |
| KPI | KPI-COM-02 |
| Excepción | lead duplicado / disqualified |

### Paso 2 — Oportunidad
| Campo | Valor |
|-------|-------|
| Actor | sales_agent |
| Entrada | prospect qualified |
| Regla | BR-COM-03 |
| Estado | opportunity open→negotiation |
| Dato | opportunity |
| Evento | Opportunity* |
| Pantalla | CRM → Opportunities |
| Endpoint | `POST/PATCH /api/v1/crm/opportunities` |
| Prueba | open/lose con razón |
| KPI | KPI-COM-01 |
| Excepción | lost prematuro |

### Paso 3 — Cotización
| Campo | Valor |
|-------|-------|
| Actor | sales_agent |
| Entrada | opportunity |
| Regla | BR-COM-02/04; moneda única |
| Estado | quotation draft→sent→accepted |
| Dato | quotation (plan/precio/add-ons) |
| Evento | Quotation* |
| Pantalla | CRM → Quotations |
| Endpoint | `/api/v1/crm/quotations` |
| Prueba | send/accept/expire |
| KPI | KPI-COM-02 |
| Excepción | expired; descuento sin aprobación |

### Paso 4 — Contrato
| Campo | Valor |
|-------|-------|
| Actor | sales_agent + sales_manager |
| Entrada | quotation accepted |
| Regla | BR-COM-01 |
| Estado | contract → signed/active |
| Dato | commercial_contract |
| Evento | ContractAccepted |
| Pantalla | Contracts |
| Endpoint | `/api/v1/contracts` |
| Prueba | approve/sign |
| KPI | KPI-COM-04 |
| Excepción | reject terms |

### Paso 5 — Organización
| Campo | Valor |
|-------|-------|
| Actor | orquestación + primer owner |
| Entrada | ContractAccepted |
| Regla | BR-ORG-02 |
| Estado | org provisioning→active |
| Dato | organization |
| Evento | OrganizationProvisioned / OrganizationActivated |
| Pantalla | Org setup |
| Endpoint | `/api/v1/organizations` |
| Prueba | provisioning con owner |
| KPI | KPI-ORG-02 |
| Excepción | fail sin owner |

### Paso 6 — Plan
| Campo | Valor |
|-------|-------|
| Actor | owner / sales asistido |
| Entrada | org active |
| Regla | BR-SUB-05 |
| Estado | plan published selected |
| Dato | plan + plan_price ref |
| Evento | PlanSelected |
| Pantalla | Choose plan |
| Endpoint | `GET /api/v1/plans` |
| Prueba | list published |
| KPI | — |
| Excepción | plan retired |

### Paso 7 — Suscripción
| Campo | Valor |
|-------|-------|
| Actor | sistema / billing_manager |
| Entrada | plan elegido |
| Regla | BR-SUB-* |
| Estado | subscription trialing\|active |
| Dato | subscription + subscription_entitlement |
| Evento | SubscriptionActivated |
| Pantalla | Subscription |
| Endpoint | `/api/v1/subscriptions` |
| Prueba | start trial/paid |
| KPI | KPI-SAAS-01 |
| Excepción | entitlements incompletos |

### Paso 8 — Factura
| Campo | Valor |
|-------|-------|
| Actor | billing |
| Entrada | RenewalDue / convert |
| Regla | BR-BILL-01/05 |
| Estado | invoice issued/open |
| Dato | invoice + items |
| Evento | InvoiceIssued |
| Pantalla | Invoices |
| Endpoint | `/api/v1/billing/invoices` |
| Prueba | no issue sin profile |
| KPI | KPI-FIN-01 |
| Excepción | profile incomplete |

### Paso 9 — Intento de pago
| Campo | Valor |
|-------|-------|
| Actor | PaymentProvider + billing |
| Entrada | invoice open |
| Regla | BR-PAY-06/03/08 |
| Estado | payment_attempt created→processing |
| Dato | payment_attempt |
| Evento | PaymentAttempt* |
| Pantalla | Checkout |
| Endpoint | `/api/v1/billing/payment-attempts` |
| Prueba | idempotency_key |
| KPI | — |
| Excepción | firma inválida |

### Paso 10 — Pago
| Campo | Valor |
|-------|-------|
| Actor | billing / platform_finance |
| Entrada | attempt succeeded |
| Regla | BR-PAY-09…12 |
| Estado | payment settled→reconciled |
| Dato | payment + payment_allocation |
| Evento | PaymentSettled |
| Pantalla | Payments |
| Endpoint | `/api/v1/billing/payments` |
| Prueba | no payment desde failed attempt |
| KPI | KPI-FIN-02 |
| Excepción | mismatch currency |

### Paso 11 — Activación
| Campo | Valor |
|-------|-------|
| Actor | orquestación |
| Entrada | PaymentSettled o trial start |
| Regla | BR-SUB-01/08 |
| Estado | access full |
| Dato | subscription_entitlement |
| Evento | EntitlementsChanged / AccessRestored |
| Pantalla | Home activado |
| Endpoint | interno orchestration |
| Prueba | features gated |
| KPI | KPI-PROD-01 |
| Excepción | pago OK pero entitlement fail |

### Paso 12 — Invitación de miembros
| Campo | Valor |
|-------|-------|
| Actor | administrator/owner |
| Entrada | org active |
| Regla | BR-ORG-03 |
| Estado | invitation pending→accepted |
| Dato | invitation + membership |
| Evento | MemberInvited/Joined |
| Pantalla | Members |
| Endpoint | `/api/v1/organizations/{id}/invitations` |
| Prueba | accept token |
| KPI | KPI-ORG-01 |
| Excepción | expired invite |

### Paso 13 — Artista
| Campo | Valor |
|-------|-------|
| Actor | artist_manager |
| Entrada | entitlement roster |
| Regla | BR-ART-01 |
| Estado | artist active |
| Dato | artist_profile + assignment |
| Evento | ArtistRegistered / ArtistActivated |
| Pantalla | Roster |
| Endpoint | `/api/v1/artists` |
| Prueba | create/assign |
| KPI | KPI-ART (roster activos) |
| Excepción | límite add-on |

### Paso 14 — Catálogo y derechos
| Campo | Valor |
|-------|-------|
| Actor | artist_manager |
| Entrada | artist/asset |
| Regla | BR-CAT-02/04/05 |
| Estado | rights approved/active |
| Dato | rights_contract + parties + territory |
| Evento | RightsApproved |
| Pantalla | Rights |
| Endpoint | `/api/v1/catalog-rights` |
| Prueba | % validation slice |
| KPI | KPI-CAT cobertura |
| Excepción | **conflicto de derechos** → disputed |

### Paso 15 — Campaña
| Campo | Valor |
|-------|-------|
| Actor | marketing_manager |
| Entrada | brief + rights OK |
| Regla | BR-CAT-01; BR-CMP-01 |
| Estado | campaign draft→… |
| Dato | campaign |
| Evento | CampaignSubmitted |
| Pantalla | Campaigns |
| Endpoint | `/api/v1/campaigns` |
| Prueba | block si disputed |
| KPI | KPI-CMP-03 |
| Excepción | rights disputed |

### Paso 16 — Aprobación de presupuesto
| Campo | Valor |
|-------|-------|
| Actor | owner/admin (+ dual) |
| Entrada | budget ≥ umbral |
| Regla | BR-CMP-02 |
| Estado | approval pending→approved |
| Dato | campaign_approval |
| Evento | ApprovalGranted |
| Pantalla | Approvals |
| Endpoint | `/api/v1/approvals` |
| Prueba | self-approve forbidden |
| KPI | — |
| Excepción | rejected → draft |

### Paso 17 — Actividad
| Campo | Valor |
|-------|-------|
| Actor | analyst / ELT |
| Entrada | schedule/events |
| Regla | BR-AN-01/02 |
| Estado | pipeline OK / report generating |
| Dato | engagement metrics (**parcial** hoy) |
| Evento | PipelineSucceeded / EngagementObserved |
| Pantalla | Analytics |
| Endpoint | `/api/v1/analytics/*` |
| Prueba | freshness gate |
| KPI | KPI-DATA-01; KPI-MUS-* |
| Excepción | stale → No disponible |

### Paso 18 — KPIs
| Campo | Valor |
|-------|-------|
| Actor | analyst |
| Entrada | datos frescos |
| Regla | BR-AN-01 |
| Estado | KpiPublished |
| Dato | KPI values etiquetados |
| Evento | KpiPublished |
| Pantalla | KPI board |
| Endpoint | `/api/v1/reporting/kpis` |
| Prueba | null → No disponible |
| KPI | catálogo |
| Excepción | denom 0 |

### Paso 19 — ROI
| Campo | Valor |
|-------|-------|
| Actor | marketing + aprobador dato |
| Entrada | spend + attr revenue |
| Regla | BR-CMP-04/05/06 |
| Estado | RoiComputed \| RoiUnavailable |
| Dato | attribution_definition + attributable_revenue_record |
| Evento | RoiComputed/Unavailable |
| Pantalla | Campaign ROI |
| Endpoint | `/api/v1/campaigns/{id}/roi` |
| Prueba | sin attr → N/D |
| KPI | KPI-CMP-01…05 |
| Excepción | **campaña sin atribución** |

### Paso 20 — Reporte
| Campo | Valor |
|-------|-------|
| Actor | analyst/dirección |
| Entrada | KPIs/ROI |
| Regla | — |
| Estado | executive_report ready |
| Dato | executive_report |
| Evento | ExecutiveReportGenerated |
| Pantalla | Executive reports |
| Endpoint | `/api/v1/reporting/reports` |
| Prueba | fail si generating error |
| KPI | — |
| Excepción | report failed |

### Paso 21 — Decisión
| Campo | Valor |
|-------|-------|
| Actor | dirección / owner |
| Entrada | report |
| Regla | — |
| Estado | business_decision approved→executed |
| Dato | business_decision |
| Evento | BusinessDecisionRecorded / DecisionApproved / DecisionExecuted |
| Pantalla | Decisions |
| Endpoint | `/api/v1/reporting/decisions` |
| Prueba | no execute rejected |
| KPI | — |
| Excepción | deferred |

### Paso 22 — Renovación o ampliación
| Campo | Valor |
|-------|-------|
| Actor | customer_success_manager + billing_manager / sales_agent (upsell) |
| Entrada | fin de periodo / health |
| Regla | BR-SUB-03; BR-PAY-04 |
| Estado | renew active \| past_due \| canceled |
| Dato | subscription_change; invoice; payment |
| Evento | SubscriptionRenewalDue / PaymentAttemptFailed / PaymentSettled / RenewalCompleted |
| Pantalla | Billing + CS |
| Endpoint | renew/checkout endpoints |
| Prueba | grace→limited→blocked |
| KPI | KPI-SAAS-06/04/05 |
| Excepción | **renovación fallida** (pago) |

---

## Variantes

### Self-service (alternativo)
Sustituye pasos 1–4 por: identity signup → organization → plan → checkout → billing_profile → subscription → invoice/payment|trial → activation (luego 12–22 igual).  
Sin prospect/opportunity/quotation/contract obligatorios.

### Pago fallido
En pasos 9–11/22: attempt failed → notify → retry → subscription past_due → access limited → blocked → recover o cancel. Org sigue `active`.

### Conflicto de derechos
En paso 14–15: rights → disputed; campaña no pasa a running; ROI no aplica hasta resolución.

### Campaña sin atribución
Paso 19: RoiUnavailable; usar KPI-CMP-02…05; no inventar dinero desde streams.

### Renovación fallida
Paso 22: PaymentAttemptFailed → past_due → limited/blocked → canceled/expired según política; CS intervención.

---

## Honestidad

Pasos 1–16, 18–22 = **diseñados/futuros**. Paso 17 actividad analítica = **parcial** hoy.
