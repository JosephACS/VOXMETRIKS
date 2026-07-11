# Opportunity Pipeline Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Refina** máquina 015 §2 (añade `qualified`, `proposal`, `canceled`).

---

## Opportunity

### Campos
`opportunity_id` · `prospect_id` · `owner_user_id` (sales_agent) · `title` · `status` · `expected_value` · `currency` · `probability` (0–100, **manual o regla configurable — no IA**) · `expected_close_date?` · `source?` · `lost_reason?` · `cancel_reason?` · `next_action?` · `next_action_due?` · `organization_id?` (post) · `primary_quotation_id?` · timestamps

### Estados
`open` · `qualified` · `proposal` · `negotiation` · `won` · `lost` · `canceled`

### Stage history
Entidad `crm_opportunity_stage_history`: from_status · to_status · changed_by · changed_at · note?

### Reglas
| ID | Regla |
|----|-------|
| BR-OPP-01 | Moneda única por opportunity (alineada a quotations hijas) |
| BR-OPP-02 | `won` requiere quotation accepted + contract accepted (o excepción auditada explícita — desaconsejada) |
| BR-OPP-03 | `lost`/`canceled` exigen razón |
| BR-OPP-04 | Probabilidad no se etiqueta como “AI score” |
| BR-OPP-05 | Reopen `lost`/`canceled` → sales_manager |
| BR-OPP-06 | Owner = sales_agent activo; reasignación auditada |
| BR-OPP-07 | Org-cliente no muta opportunity |

### Pipeline board (UI)
Columnas = estados abiertos (`open`…`negotiation`); cerrados en lista aparte.

### KPI
pipeline_value · opportunities_by_stage · win_rate · loss_rate · average_sales_cycle · (sin inventar valores).
