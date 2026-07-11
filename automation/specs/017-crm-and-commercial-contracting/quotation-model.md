# Quotation Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Refina** máquina 015 §3 con versionado y estados de aprobación.

---

## Entidades

### quotation (cabecera)
`quotation_id` · `opportunity_id` · `currency` · `status` · `current_version_no` · `valid_until?` · `organization_id?` · timestamps · `created_by`

### quotation_version (inmutable tras sent)
`quotation_version_id` · `quotation_id` · `version_no` · `status` · `terms_snapshot` (JSON/texto versionado) · `proposed_discount_pct?` · `proposed_discount_amount?` · `subtotal` · `total` · `sent_at?` · `accepted_at?` · `rejected_at?` · `superseded_at?` · `created_by` · `created_at`  
**Inmutable** cuando status ∈ {sent, accepted, rejected, expired, superseded} (campos de negocio).

### quotation_item
`item_id` · `quotation_version_id` · `line_no` · `description` · `plan_code?` (**referencia conceptual futura** — no crea plan/subscription) · `quantity` · `unit_price` · `amount` · `currency` (debe = cabecera)

### proposed_discount
Puede vivir en version fields o sub-entidad; umbral dispara `approval_request`.

---

## Estados (cabecera / versión alineados)

`draft` · `pending_approval` · `approved` · `sent` · `accepted` · `rejected` · `expired` · `superseded` · `canceled`

---

## Reglas

| ID | Regla |
|----|-------|
| BR-QUO-01 | Una cotización = una moneda |
| BR-QUO-02 | Post-`sent`: no editar versión; nueva edición → nueva version (+ supersede anterior si aplica) |
| BR-QUO-03 | Descuento ≥ umbral → `pending_approval` antes de `sent` |
| BR-QUO-04 | No crear subscription / invoice / payment |
| BR-QUO-05 | `plan_code` no implica plan publicado existente (validación soft/futura) |
| BR-QUO-06 | Accept de versión `expired` = inválido |
| BR-QUO-07 | Solo una versión `accepted` activa por opportunity (o política 1 accepted current) |
| BR-QUO-08 | Precios = configurables/propuestos; **no** catálogo definitivo |

---

## KPI
quote_acceptance_rate · discount_rate (sobre accepted) — madurez **Propuesto**.
