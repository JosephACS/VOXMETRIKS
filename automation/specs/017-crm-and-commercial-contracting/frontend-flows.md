# Frontend Flows (diseño) — Spec 017

**Status**: DESIGN_APPROVED · **IMPLEMENTATION_PENDING**  
CRM **interno** VOXMETRIKS. Sin billing UI. Sin portal cliente CRM.

---

## Navegación propuesta

```text
/app/crm                     → dashboard
/app/crm/prospects           → list
/app/crm/prospects/:id       → detail + contacts + timeline
/app/crm/contacts/:id        → contact detail
/app/crm/opportunities       → board | list
/app/crm/opportunities/:id   → detail + activities + quotes
/app/crm/quotations/:id      → editor / version viewer
/app/crm/approvals           → inbox
/app/crm/contracts/:id       → contract detail + accept
/app/crm/conversions/new     → wizard
/app/crm/opportunities/:id/lost → lost flow
/app/crm/audit               → history
```

Guards: autenticado + permiso CRM platform (no organizationRequiredGuard de cliente).

---

## Pantallas

### CRM dashboard
KPI widgets **vacíos/honestos** hasta datos (N/D si cero fuentes). Pipeline snapshot. Inbox approvals count.

### Prospect list/detail
Filtros status/owner/source. Acciones transition. Panel contacts. Flag duplicates.

### Contact detail
Flags decision/signatory/primary. Consent badge solo si `consent_recorded`. CTA “link existing user” opcional (no create user).

### Opportunity board/list
Kanban por stage. Drag = transition API. Lost/cancel modals con razón.

### Activity timeline
Composer tipado; email_reference = URL/subject only.

### Quotation editor / version viewer
Draft editable; sent = read-only; “New version” CTA. Currency lock. Discount → approval banner.

### Approval inbox
Decide approve/reject + note.

### Contract detail
Terms snapshot; accept form (evidence). Disclaimer: aceptación académica ≠ firma legal certificada.

### Conversion wizard
Steps: validate prerequisites → create|link org → owner/invite → confirm → result (org id, invite).  
No plan picker de cobro.

### Lost opportunity flow
Reason codes + note.

### Audit history
Filtros entity/actor/date; payloads sanitizados.

---

## Estados UI especiales

| Estado | UI |
|--------|-----|
| Sin permiso CRM | access denied (no datos) |
| Quotation expired | badge + block accept |
| Approval pending | block send |
| Conversion succeeded | link to org 016 settings (read) |
| Org-cliente user | no entradas menú CRM |

---

## i18n
Claves `crm.*` futuras; no implementar ahora.

---

## OUT UI
Billing · invoices · payment methods · plan catalog admin · campaigns · CS health.
