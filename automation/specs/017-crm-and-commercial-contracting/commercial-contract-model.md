# Commercial Contract Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**No es** subscription · **No es** rights_contract · **No afirma** firma electrónica legal.

---

## commercial_contract

### Campos
`contract_id` · `quotation_id` (versión accepted) · `opportunity_id` · `prospect_id` · `organization_id?` (futura o existente) · `customer_legal_name` · `authorized_signatory_contact_id` · `currency` · `effective_date?` · `term_months?` · `renewal_intent?` (`renew`|`negotiate`|`unknown`) · `terms_snapshot` · `status` · `accepted_at?` · `acceptance_evidence` (texto/ref académica: actor, canal, nota) · `accepted_by_user_id?` · timestamps

### Estados
`draft` · `pending_approval` · `approved` · `sent` · `accepted` · `active_handoff` · `rejected` · `expired` · `terminated`

| Estado | Significado |
|--------|-------------|
| accepted | Aceptación académica registrada |
| active_handoff | Listo / en curso de conversión a org + handoff subscriptions (**sin** activar plan) |
| terminated | Fin comercial documentado |

---

## Aceptación académica

Registro mínimo: actor · timestamp · evidencia (nota, referencia externa, checkbox confirmado en UI interna).  
**No** afirmar validez legal de e-sign ni compliance.

---

## Reglas

| ID | Regla |
|----|-------|
| BR-CTR-01 | Requiere quotation `accepted` vigente |
| BR-CTR-02 | No crear invoice/payment/subscription |
| BR-CTR-03 | Signatory = contact con `is_authorized_signatory` |
| BR-CTR-04 | Aprobación interna si términos no estándar |
| BR-CTR-05 | `accepted` → puede disparar conversión (saga) |
| BR-CTR-06 | Distinguir de `rights_contract` (catálogo) |

---

## KPI
contracts_accepted · conversion_time (accepted → org linked).
