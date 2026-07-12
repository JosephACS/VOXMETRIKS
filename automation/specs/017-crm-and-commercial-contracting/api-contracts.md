# API Contracts — Spec 017

**Status**: DESIGN_APPROVED · **IMPLEMENTED** (J3) · CLOSED_WITH_ACCEPTED_DEBT  
**Base:** `/api/v1/crm` · Auth: Bearer + platform RBAC permission

Prefijo propuesto: `/api/v1/crm/...` (+ opcional `/api/v1/crm/contracts` — HUM006).

---

## Códigos HTTP comunes

| Código | Uso |
|--------|-----|
| 400 | body inválido / fuentes contradictorias |
| 401 | no autenticado |
| 403 | sin permiso CRM / org-cliente intentando CRM |
| 404 | no encontrado (anti-enum donde aplique) |
| 409 | duplicado / conflict stage / double conversion |
| 410 | expired quotation/approval/contract |
| 422 | validación campos/estados |
| 501 | no aplica (reservado; no usar para fingir billing) |

Idempotency-Key: `POST` create prospect (opcional), create quotation, convert.

---

## Prospects

| Method | Path | Permiso | Actor |
|--------|------|---------|-------|
| GET | `/crm/prospects` | crm.prospect.view | sales_* |
| POST | `/crm/prospects` | crm.prospect.create | sales_agent+ |
| GET | `/crm/prospects/{id}` | crm.prospect.view | |
| PATCH | `/crm/prospects/{id}` | crm.prospect.update | |
| POST | `/crm/prospects/{id}/transition` | crm.prospect.update | body: to_status, reason? |

Request create: display_name, source?, owner_user_id?  
Response: prospect DTO + status.  
Audit: create/update/transition.  
Paginación: cursor/limit.

---

## Contacts

| Method | Path | Permiso |
|--------|------|---------|
| GET/POST | `/crm/contacts` | view via prospect / create update |
| GET/PATCH | `/crm/contacts/{id}` | |
| POST | `/crm/prospects/{id}/contacts` | link contact |

No endpoint “create user from contact”.

---

## Opportunities

| Method | Path | Permiso |
|--------|------|---------|
| GET/POST | `/crm/opportunities` | opportunity.view/create |
| GET/PATCH | `/crm/opportunities/{id}` | view/update |
| POST | `/crm/opportunities/{id}/transition` | update/close |
| GET | `/crm/opportunities/{id}/stage-history` | view |

Errors: 422 invalid transition; 409 won sin prerequisites.

---

## Activities

| Method | Path | Permiso |
|--------|------|---------|
| GET | `/crm/activities?opportunity_id=` | activity.manage o view bundled |
| POST | `/crm/activities` | crm.activity.manage |
| PATCH | `/crm/activities/{id}` | manage |

No `POST /crm/emails/send`.

---

## Quotations

| Method | Path | Permiso |
|--------|------|---------|
| GET/POST | `/crm/quotations` | quotation.* |
| GET | `/crm/quotations/{id}` | |
| POST | `/crm/quotations/{id}/versions` | create/update draft |
| GET | `/crm/quotations/{id}/versions/{n}` | view |
| POST | `/crm/quotations/{id}/submit-approval` | update |
| POST | `/crm/quotations/{id}/send` | quotation.send |
| POST | `/crm/quotations/{id}/accept` | update (interno) |
| POST | `/crm/quotations/{id}/reject` | update |

Errors: 409 edit sent; 410 accept expired; 403 send sin approval.

---

## Approvals

| Method | Path | Permiso |
|--------|------|---------|
| GET | `/crm/approvals?status=pending` | quotation.approve / contract.approve / manager |
| POST | `/crm/approvals/{id}/decide` | approve perms | body: approved\|rejected, note |

---

## Contracts

| Method | Path | Permiso |
|--------|------|---------|
| GET/POST | `/crm/contracts` | contract.create / view |
| GET/PATCH | `/crm/contracts/{id}` | |
| POST | `/crm/contracts/{id}/submit` | create |
| POST | `/crm/contracts/{id}/approve` | contract.approve |
| POST | `/crm/contracts/{id}/send` | create |
| POST | `/crm/contracts/{id}/accept` | contract.accept | body: evidence |

---

## Conversion

| Method | Path | Permiso |
|--------|------|---------|
| POST | `/crm/conversions` | customer.convert | Idempotency-Key required |
| GET | `/crm/conversions/{id}` | view + convert |

Request: opportunity_id, contract_id, mode create_org|link_existing, organization_id?, owner_email/user_id, slug?, display_name?  
Response: conversion_id, organization_id, invitation_id?, status.  
Errors: 409 already converted; 422 missing signatory/owner; 403.

Audit: Conversion* + org events 016.

---

## Audit

| Method | Path | Permiso |
|--------|------|---------|
| GET | `/crm/audit` | crm.audit.view |

---

## Fuera de API 017

`/subscriptions`, `/invoices`, `/payments`, `/plans` publish, checkout self-service.
