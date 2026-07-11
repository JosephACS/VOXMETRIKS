# Business State Machines — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  

Separación conceptual obligatoria:

| Concepto | Estados |
|----------|---------|
| **Organization lifecycle** | `provisioning` · `active` · `suspended_by_platform` · `closed` |
| **Subscription lifecycle** | `trialing` · `active` · `past_due` · `canceled` · `expired` |
| **Access / entitlements** | `full` · `limited` · `blocked` |

La mora afecta **subscription** y **access**, no la identidad de la organización.

Cada transición: origen · acción · actor · condición · destino · evento · auditoría · notificación · operación prohibida.

---

## 1. Prospecto

Estados: `new` · `contacted` · `qualified` · `disqualified` · `converted`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| new | contact | sales_agent | — | contacted | ProspectContacted | sí | opcional | convertir sin qualify |
| contacted | qualify | sales_agent | datos mínimos | qualified | ProspectQualified | sí | — | qualify sin contacto |
| contacted | disqualify | sales_agent | razón | disqualified | ProspectDisqualified | sí | — | reabrir sin sales_manager |
| qualified | disqualify | sales_agent | razón | disqualified | ProspectDisqualified | sí | — | — |
| qualified | convert | sales_agent | opportunity won path | converted | ProspectConverted | sí | CS onboarding | convert sin opportunity |
| disqualified | reopen | sales_manager | justificación | contacted | ProspectReopened | sí | — | reopen por org owner |

Scope: **platform** (sin `org_id` hasta conversión).

---

## 2. Oportunidad

Estados: `open` · `negotiation` · `won` · `lost`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| open | start_negotiation | sales_agent | quotation draft/sent | negotiation | OpportunityNegotiation | sí | — | win directo desde open |
| negotiation | win | sales_agent | quotation accepted + contract path | won | OpportunityWon | sí | — | win sin quotation accepted (salvo excepción auditada) |
| open | lose | sales_agent | razón obligatoria | lost | OpportunityLost | sí | — | lose sin razón |
| negotiation | lose | sales_agent | razón | lost | OpportunityLost | sí | — | — |
| lost | reopen | sales_manager | justificación | open | OpportunityReopened | sí | — | reopen por cliente org |

---

## 3. Cotización

Estados: `draft` · `sent` · `accepted` · `rejected` · `expired`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| draft | send | sales_agent | ítems+moneda única | sent | QuotationSent | sí | al prospect | send multi-currency |
| sent | accept | sales_agent/sistema | no expired | accepted | QuotationAccepted | sí | sales_manager | accept si expired |
| sent | reject | sales_agent | razón | rejected | QuotationRejected | sí | — | — |
| sent | expire | sistema | past valid_until | expired | QuotationExpired | sí | sales_agent | accept expired |
| draft | discard | sales_agent | — | rejected | QuotationDiscarded | sí | — | discard accepted |

---

## 4. Contrato comercial

Estados: `draft` · `pending_approval` · `approved` · `signed` · `active` · `terminated`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| draft | submit | sales_agent | quotation accepted | pending_approval | ContractSubmitted | sí | approver | submit sin quotation |
| pending_approval | approve | sales_manager / platform_finance | términos OK | approved | ContractApproved | sí | sales_agent | approve por org owner cliente |
| pending_approval | reject | sales_manager | razón | draft | ContractRejected | sí | sales_agent | — |
| approved | sign | sales_agent + counterparty | firma | signed | ContractAccepted | sí | ops/CS | — |
| signed | activate | orquestación | org provisioning started | active | ContractActivated | sí | — | activate sin org link |
| active | terminate | sales_manager / legal-design | razón | terminated | ContractTerminated | sí | partes | terminate silencioso |

---

## 5. Organización

Estados: `provisioning` · `active` · `suspended_by_platform` · `closed`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | create | orquestación / signup | contract o self-serve | provisioning | OrganizationProvisioned | sí | owner | crear sin identity |
| provisioning | activate | orquestación | owner asignado | active | OrganizationActivated | sí | onboarding | activate sin owner |
| active | suspend_platform | platform_admin / security | incidente/política | suspended_by_platform | OrganizationSuspendedByPlatform | sí | owners | suspender por mora de pago |
| suspended_by_platform | reinstate | platform_admin | incidente cerrado | active | OrganizationReinstated | sí | owners | reinstate sin review |
| active | close | owner + platform | offboarding | closed | OrganizationClosed | sí | members | close con invoices abiertas sin plan |
| suspended_by_platform | close | platform_admin | — | closed | OrganizationClosed | sí | — | — |

**Prohibido global:** transicionar org a “past_due/limited” — eso es subscription/access.

---

## 6. Invitación

Estados: `pending` · `accepted` · `expired` · `revoked`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | invite | administrator/owner | org active; email | pending | MemberInvited | sí | invitee | invite si org suspended_by_platform/closed |
| pending | accept | invitee | token válido | accepted | MemberJoined | sí | admin | accept expired token |
| pending | expire | sistema | TTL | expired | InviteExpired | sí | admin | — |
| pending | revoke | administrator | — | revoked | InviteRevoked | sí | invitee | — |

---

## 7. Suscripción

Estados: `trialing` · `active` · `past_due` · `canceled` · `expired`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | start_trial | owner/billing_manager/sistema | plan permite trial | trialing | SubscriptionActivated | sí | owner | trial sin org |
| (none) | start_paid | sistema | payment settled o invoice policy | active | SubscriptionActivated | sí | owner | — |
| trialing | convert | sistema/owner | pago OK o fin trial con método | active | SubscriptionActivated | sí | — | — |
| trialing | cancel | owner | política | canceled | SubscriptionCanceled | sí | — | — |
| trialing | expire_trial | sistema | trial end sin convert | expired | SubscriptionExpired | sí | owner | — |
| active | mark_past_due | billing/orquestación | PaymentAttemptFailed / invoice past_due | past_due | SubscriptionPastDue | sí | billing_manager | marcar org suspended |
| past_due | recover | sistema | PaymentSettled (+ RenewalCompleted si ciclo) | active | SubscriptionRecovered | sí | owner | — |
| past_due | cancel | owner/sistema | política mora | canceled | SubscriptionCanceled | sí | — | — |
| active | cancel | owner | política end-of-term/immediate | canceled | SubscriptionCanceled | sí | — | — |
| canceled | expire | sistema | fin derechos residuales | expired | SubscriptionExpired | sí | — | reactivar silenciosa |
| expired | resubscribe | owner | nuevo ciclo | trialing/active | SubscriptionResubscribed | sí | — | mutar expired in-place sin change |

Access paralelo (máquina 19b integrada abajo como §19 Access): past_due puede forzar `limited` luego `blocked` sin cambiar org lifecycle.

---

## 8. Factura (invoice)

Estados: `draft` · `issued/open` · `partially_paid` · `paid` · `past_due` · `void` · `partially_credited` · `credited`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | create_draft | billing | billing_profile; moneda única | draft | InvoiceDrafted | sí | — | draft multi-currency |
| draft | issue | billing | ítems válidos | issued/open | InvoiceIssued | sí | payer | issue sin profile |
| issued/open | allocate_partial | billing | payment_allocation < balance | partially_paid | InvoicePartiallyPaid | sí | — | — |
| partially_paid | allocate_full | billing | balance 0 | paid | InvoicePaid | sí | owner | — |
| issued/open | allocate_full | billing | balance 0 | paid | InvoicePaid | sí | owner | — |
| issued/open | mark_past_due | sistema | after due_at unpaid | past_due | InvoicePastDue | sí | payer | — |
| past_due | allocate_partial | billing | — | partially_paid | InvoicePartiallyPaid | sí | — | — |
| past_due | allocate_full | billing | — | paid | InvoicePaid | sí | — | — |
| draft | void | finance | nunca issued | void | InvoiceVoided | sí | — | void paid |
| issued/open | void | finance+aprobación | no payments / policy | void | InvoiceVoided | sí | — | void si paid/partially_paid |
| paid | credit_partial | finance | credit_note < total | partially_credited | InvoicePartiallyCredited | sí | — | credit > paid |
| paid | credit_full | finance | credit_note = total | credited | InvoiceCredited | sí | — | — |
| partially_credited | credit_rest | finance | — | credited | InvoiceCredited | sí | — | edit amounts destructively |

---

## 9. Intento de pago (payment_attempt)

Estados: `created` · `processing` · `succeeded` · `failed` · `canceled`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | create | billing | idempotency_key única | created | PaymentAttemptCreated | sí | — | create sin idempotency_key |
| created | submit | PaymentProvider | — | processing | PaymentAttemptProcessing | sí | — | — |
| processing | succeed | provider/webhook | firma OK; monto/moneda match | succeeded | PaymentAttemptSucceeded | sí | — | succeed con firma inválida |
| processing | fail | provider/webhook | rechazo | failed | PaymentAttemptFailed | sí | payer | — |
| processing | cancel | finance/sistema | timeout/user | canceled | PaymentAttemptCanceled | sí | — | — |
| created | cancel | finance | antes de submit | canceled | PaymentAttemptCanceled | sí | — | reusar same key con otro monto |

**Nota:** `failed` vive aquí, no como estado ambiguo de `payment`.

---

## 10. Pago (payment)

Estados: `recorded/authorized` · `settled` · `reconciled` · `partially_refunded` · `refunded` · `reversed`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | record | billing | attempt succeeded | recorded/authorized | PaymentRecorded | sí | — | crear payment desde attempt failed |
| recorded/authorized | settle | billing/provider | fondos confirmados | settled | PaymentSettled | sí | — | — |
| settled | reconcile | platform_finance/finance | conciliación explícita | reconciled | PaymentReconciled | sí | — | auto-reconcile sin proceso |
| settled/reconciled | refund_partial | finance | refund < amount | partially_refunded | PaymentPartiallyRefunded | sí | payer | — |
| partially_refunded | refund_rest | finance | — | refunded | PaymentRefunded | sí | — | — |
| settled/reconciled | refund_full | finance | — | refunded | PaymentRefunded | sí | payer | — |
| settled/reconciled | reverse | platform_finance | chargeback/error | reversed | PaymentReversed | sí | finance | borrar payment row |

No existe estado `failed` en payment: el fallo es de `payment_attempt`.

---

## 11. Reembolso (refund)

Estados: `requested` · `approved` · `processing` · `completed` · `rejected`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | request | finance | payment settled/reconciled | requested | RefundRequested | sí | — | refund attempt failed |
| requested | approve | finance / platform_finance | umbral | approved | RefundApproved | sí | — | auto-approve sobre umbral |
| requested | reject | finance | razón | rejected | RefundRejected | sí | requester | — |
| approved | process | PaymentProvider | — | processing | RefundProcessing | sí | — | — |
| processing | complete | webhook | provider_event_id único | completed | RefundCompleted | sí | payer | doble refund mismo event |
| processing | fail_reject | provider | — | rejected | RefundFailed | sí | finance | — |

---

## 12. Artista

Estados: `draft` · `active` · `inactive` · `archived`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | create | artist_manager | org active | draft | ArtistRegistered | sí | — | create en org closed |
| draft | activate | artist_manager | perfil mínimo | active | ArtistActivated | sí | assignee | — |
| active | deactivate | artist_manager | — | inactive | ArtistDeactivated | sí | — | — |
| inactive | activate | artist_manager | — | active | ArtistActivated | sí | — | — |
| inactive/active | archive | artist_manager+review | rights check | archived | ArtistArchived | sí | — | archive con disputed rights sin nota |

---

## 13. Contrato de catálogo (rights_contract)

Estados: `draft` · `in_review` · `approved` · `rejected` · `active` · `expired` · `disputed`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| draft | submit | artist_manager | parties+% | in_review | RightsSubmitted | sí | approver | submit si % inválido |
| in_review | approve | administrator | validación 100% por asset+type+territory+periodo | approved | RightsApproved | sí | — | approve con overlap conflict |
| in_review | reject | administrator | razón | rejected | RightsRejected | sí | manager | — |
| approved | activate | sistema/admin | valid_from | active | RightsActivated | sí | — | — |
| active | dispute | administrator/auditor | conflicto | disputed | RightsConflictDetected | sí | marketing | usar en campaña |
| disputed | resolve_approve | administrator | resolución | active | RightsResolved | sí | — | resolve sin audit |
| active | expire | sistema | valid_to | expired | RightsExpired | sí | manager | — |

---

## 14. Campaña

Estados: `draft` · `pending_approval` · `approved` · `running` · `paused` · `completed` · `canceled`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| draft | submit | marketing_manager | rights OK | pending_approval | CampaignSubmitted | sí | approver | submit con rights disputed |
| draft | run_direct | marketing_manager | bajo umbral | running | CampaignStarted | sí | — | bypass umbral |
| pending_approval | approve | owner/admin | — | approved | CampaignApproved | sí | marketing | — |
| pending_approval | reject | owner/admin | razón | draft | CampaignRejected | sí | marketing | — |
| approved | start | marketing_manager | — | running | CampaignStarted | sí | — | — |
| running | pause | marketing_manager | — | paused | CampaignPaused | sí | — | — |
| paused | resume | marketing_manager | — | running | CampaignResumed | sí | — | — |
| running | complete | marketing_manager | resultados | completed | CampaignClosed | sí | dirección | — |
| * | cancel | owner/marketing | razón | canceled | CampaignCanceled | sí | — | cancel completed |

---

## 15. Aprobación (genérica)

Estados: `pending` · `approved` · `rejected` · `expired`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | request | requester | objeto ligado | pending | ApprovalRequested | sí | approver | self-approve si política lo prohíbe |
| pending | approve | approver | rol adecuado | approved | ApprovalGranted | sí | requester | — |
| pending | reject | approver | razón | rejected | ApprovalRejected | sí | requester | — |
| pending | expire | sistema | TTL | expired | ApprovalExpired | sí | requester | approve expired |

---

## 16. Ticket

Estados: `new` · `triaged` · `in_progress` · `waiting_customer` · `escalated` · `resolved` · `closed`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | create | user/support | — | new | TicketCreated | sí | support | — |
| new | triage | support_agent | clasificación | triaged | TicketTriaged | sí | — | — |
| triaged | start | support_agent | — | in_progress | TicketInProgress | sí | requester | — |
| in_progress | wait | support_agent | falta info | waiting_customer | TicketWaiting | sí | requester | — |
| waiting_customer | resume | support_agent | respuesta | in_progress | TicketResumed | sí | — | — |
| in_progress | escalate | support_agent | billing/security/tech | escalated | TicketEscalated | sí | target role | escalate security sin flag |
| escalated | resolve | assignee | — | resolved | TicketResolved | sí | requester | — |
| in_progress | resolve | support_agent | — | resolved | TicketResolved | sí | requester | — |
| resolved | close | support_agent/sistema | CSAT opcional | closed | TicketClosed | sí | — | — |
| closed | reopen | support_agent | justificación | in_progress | TicketReopened | sí | — | — |

---

## 17. Health score

Estados: `healthy` · `watch` · `risk` · `critical`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| * | recompute | sistema/CSM | snapshot | healthy/watch/risk/critical | HealthChanged | sí | CSM si risk+ | inventar score sin datos |
| critical | intervene | CSM | — | (estado puede seguir critical) | InterventionOpened | sí | owner | — |

---

## 18. Reporte ejecutivo

Estados: `requested` · `generating` · `ready` · `failed` · `archived`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | request | analyst/owner | — | requested | ReportRequested | sí | — | — |
| requested | generate | sistema | — | generating | ReportGenerating | sí | — | — |
| generating | succeed | sistema | freshness OK | ready | ExecutiveReportGenerated | sí | requester | publicar si stale sin label |
| generating | fail | sistema | error | failed | ReportFailed | sí | requester | — |
| ready | archive | analyst | — | archived | ReportArchived | sí | — | — |
| failed | retry | analyst | — | generating | ReportRetry | sí | — | — |

---

## 19. Decisión empresarial

Estados: `proposed` · `approved` · `rejected` · `deferred` · `executed`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| (none) | propose | dirección/analyst | evidencia | proposed | BusinessDecisionRecorded | sí | approvers | — |
| proposed | approve | owner/dirección | — | approved | DecisionApproved | sí | — | — |
| proposed | reject | owner/dirección | razón | rejected | DecisionRejected | sí | proposer | — |
| proposed | defer | owner/dirección | — | deferred | DecisionDeferred | sí | — | — |
| deferred | propose_again | proposer | — | proposed | DecisionReopened | sí | — | — |
| approved | execute | assignee | — | executed | DecisionExecuted | sí | — | execute rejected |

---

## 19b. Access / entitlements (complementaria — requerida por separación mora)

Estados: `full` · `limited` · `blocked`

| Origen | Acción | Actor | Condición | Destino | Evento | Auditoría | Notificación | Operación prohibida |
|--------|--------|-------|-----------|---------|--------|-----------|--------------|---------------------|
| full | limit | orquestación | subscription past_due / gracia | limited | AccessLimited | sí | owner | set org=suspended |
| limited | block | orquestación | fin gracia / policy | blocked | AccessBlocked | sí | owner | — |
| limited | restore | orquestación | PaymentSettled | full | AccessRestored | sí | owner | — |
| blocked | restore | orquestación | recover payment + policy | full | AccessRestored | sí | owner | restore sin pago si policy lo exige |
| full | block | platform_admin | security | blocked | AccessBlockedByPlatform | sí | owner | — |

Esta máquina opera sobre **entitlements/access**, no sobre organization lifecycle.

---

## Catálogo canónico de eventos (nombres normalizados)

Usar **exactamente** estos nombres en todos los documentos de la 015:

| Evento canónico | Uso |
|-----------------|-----|
| ProspectQualified | Prospecto calificado |
| OpportunityWon | Oportunidad ganada |
| ContractAccepted | Contrato comercial aceptado/firmado (antes: ContractSigned) |
| OrganizationProvisioned | Org creada en provisioning (antes: OrgProvisioned) |
| OrganizationActivated | Org pasa a active |
| SubscriptionActivated | Suscripción iniciada o convertida a activa |
| InvoiceIssued | Factura emitida |
| PaymentAttemptFailed | Intento de pago fallido (no confundir con payment) |
| PaymentSettled | Pago asentado |
| PaymentReconciled | Conciliación explícita |
| AccessLimited | Acceso limitado por mora/gracia |
| ArtistRegistered | Alta de artista (antes: ArtistCreated) |
| RightsConflictDetected | Conflicto de derechos (antes: RightsDisputed) |
| CampaignApproved | Campaña aprobada |
| CampaignClosed | Campaña cerrada/completada (antes: CampaignCompleted) |
| ExecutiveReportGenerated | Reporte ejecutivo listo (antes: ReportReady) |
| BusinessDecisionRecorded | Decisión empresarial registrada |
| RenewalCompleted | Renovación completada con éxito |

Alias históricos **no usar** en docs nuevos: `OrgProvisioned`, `ContractSigned`, `PaymentFailed` (usar PaymentAttemptFailed), `ArtistCreated`, `RightsDisputed`, `CampaignCompleted`, `ReportReady`.

## Conteo de transiciones documentadas

| Máquina | Transiciones (filas) |
|---------|---------------------:|
| 1 Prospecto | 6 |
| 2 Oportunidad | 5 |
| 3 Cotización | 5 |
| 4 Contrato | 6 |
| 5 Organización | 6 |
| 6 Invitación | 4 |
| 7 Suscripción | 11 |
| 8 Factura | 14 |
| 9 payment_attempt | 6 |
| 10 payment | 7 |
| 11 refund | 6 |
| 12 artista | 5 |
| 13 rights_contract | 7 |
| 14 campaña | 9 |
| 15 aprobación | 4 |
| 16 ticket | 10 |
| 17 health | 2 |
| 18 reporte | 6 |
| 19 decisión | 6 |
| 19b access | 5 |
| **Total** | **130** |
