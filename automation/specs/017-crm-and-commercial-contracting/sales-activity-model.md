# Sales Activity Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Tipos

| Tipo | Descripción | Canal real |
|------|-------------|------------|
| `note` | Nota libre | — |
| `call` | Llamada registrada | metadatos |
| `meeting` | Reunión | metadatos |
| `email_reference` | Referencia a email enviado fuera del sistema | **no** envío SMTP en 017 |
| `task` | Tarea asignable | — |
| `follow_up` | Seguimiento con due date | — |

---

## Campos

`activity_id` · `activity_type` · `actor_user_id` · `occurred_at` · `subject?` · `body?` · `outcome?` · `next_action?` · `next_action_due?` · `prospect_id?` · `contact_id?` · `opportunity_id?` · `status` (`open`|`done`|`canceled`) · timestamps

Al menos una FK a prospect | contact | opportunity.

---

## Reglas

| ID | Regla |
|----|-------|
| BR-ACT-01 | Toda actividad auditable (quién/cuándo/qué) |
| BR-ACT-02 | No implementar envío real de email |
| BR-ACT-03 | Permiso `crm.activity.manage` |
| BR-ACT-04 | No borrar físico; soft cancel |
| BR-ACT-05 | PII en body sujeta a retención comercial |

---

## Timeline UI
Orden cronológico inverso en prospect/opportunity detail.
