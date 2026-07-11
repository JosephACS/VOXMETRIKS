# Lifecycle State Machines — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
Cada transición: origen · acción · actor · condición · destino · evento · auditoría · prohibido.

---

## 1. Prospect

Estados: `lead`/`new` · `contacted` · `qualified` · `disqualified` · `converted`

| Origen | Acción | Actor | Condición | Destino | Evento | Audit | Prohibido |
|--------|--------|-------|-----------|---------|--------|-------|-----------|
| (none) | create | sales_agent | — | lead/new | ProspectCreated | sí | create por org owner |
| lead/new | contact | sales_agent | — | contacted | ProspectContacted | sí | — |
| contacted | qualify | sales_agent | datos mínimos | qualified | ProspectQualified | sí | qualify sin contacto |
| *open | disqualify | sales_agent | razón | disqualified | ProspectDisqualified | sí | sin razón |
| qualified | convert_mark | sistema | conversion succeeded | converted | ProspectConverted | sí | convert sin conversion |
| disqualified | reopen | sales_manager | justificación | contacted | ProspectReopened | sí | reopen por cliente |

---

## 2. Opportunity

Estados: `open` · `qualified` · `proposal` · `negotiation` · `won` · `lost` · `canceled`

| Origen | Acción | Actor | Condición | Destino | Evento | Audit | Prohibido |
|--------|--------|-------|-----------|---------|--------|-------|-----------|
| (none) | open | sales_agent | prospect qualified (recomendado) | open | OpportunityOpened | sí | — |
| open | qualify | sales_agent | — | qualified | OpportunityStageChanged | sí | — |
| qualified | propose | sales_agent | quotation draft/approved | proposal | OpportunityStageChanged | sí | — |
| proposal | negotiate | sales_agent | quotation sent | negotiation | OpportunityStageChanged | sí | — |
| negotiation | win | sales_agent/sistema | quotation+contract accepted | won | OpportunityWon | sí | win sin accept |
| *open | lose | sales_agent | razón | lost | OpportunityLost | sí | lose sin razón |
| *open | cancel | sales_agent | razón | canceled | OpportunityCanceled | sí | — |
| lost/canceled | reopen | sales_manager | justificación | open | OpportunityReopened | sí | reopen cliente |

\*open = cualquier estado no terminal.

---

## 3. Quotation / version

| Origen | Acción | Actor | Condición | Destino | Evento | Audit | Prohibido |
|--------|--------|-------|-----------|---------|--------|-------|-----------|
| (none) | create_draft | sales_agent | opp abierta | draft | QuotationVersionCreated | sí | multi-currency |
| draft | request_approval | sales_agent | discount≥threshold | pending_approval | ApprovalRequested | sí | send sin approve |
| pending_approval | approve | sales_manager | — | approved | ApprovalDecided | sí | self-approve umbral |
| pending_approval | reject | sales_manager | razón | draft | ApprovalDecided | sí | — |
| draft/approved | send | sales_agent | ítems+moneda; approvals OK | sent | QuotationSent | sí | editar sent |
| sent | accept | sales_agent/sistema | not expired | accepted | QuotationAccepted | sí | accept expired |
| sent | reject | sales_agent | razón | rejected | QuotationRejected | sí | — |
| sent | expire | sistema | past valid_until | expired | QuotationExpired | sí | — |
| draft | revise | sales_agent | — | new version draft; old superseded si sent | QuotationSuperseded | sí | mutar sent in-place |
| * | cancel | sales_agent | no accepted | canceled | QuotationCanceled | sí | cancel accepted sin proceso |

---

## 4. Approval

| Origen | Acción | Actor | Destino | Evento |
|--------|--------|-------|---------|--------|
| (none) | request | sales_agent | pending | ApprovalRequested |
| pending | approve | sales_manager | approved | ApprovalDecided |
| pending | reject | sales_manager | rejected | ApprovalDecided |
| pending | cancel | requester/manager | canceled | ApprovalCanceled |
| pending | expire | sistema | expired | ApprovalExpired |

---

## 5. Commercial contract

| Origen | Acción | Actor | Condición | Destino | Evento | Prohibido |
|--------|--------|-------|-----------|---------|--------|-----------|
| (none) | draft | sales_agent | quotation accepted | draft | ContractDrafted | sin quotation |
| draft | submit | sales_agent | — | pending_approval | ContractSubmitted | — |
| pending_approval | approve | sales_manager | — | approved | ContractApproved | approve cliente |
| pending_approval | reject | sales_manager | razón | draft/rejected | ContractRejected | — |
| approved | send | sales_agent | — | sent | ContractSent | — |
| sent/approved | accept | sales_agent + evidence | signatory OK | accepted | ContractAccepted | e-sign legal claim |
| accepted | handoff | sistema | conversion start/success | active_handoff | OrganizationLinkedFromCrm | crear sub |
| * | expire | sistema | policy | expired | ContractExpired | — |
| *non-term | terminate | sales_manager | razón | terminated | ContractTerminated | silencioso |

---

## 6. Conversion

| Origen | Acción | Actor | Destino | Evento |
|--------|--------|-------|---------|--------|
| (none) | start | sales_agent/manager + convert perm | started | ConversionStarted |
| started | succeed | sistema | succeeded | CustomerConverted |
| started | fail | sistema | failed | ConversionFailed |
| failed | retry | sales_agent | started | ConversionRetried |

Organización resultante sigue máquina 016 (`provisioning`→`active`).

---

## Separación global

Mora / subscription / access **no** aparecen en estas máquinas (OUT).
