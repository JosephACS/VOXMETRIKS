# Approval Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## approval_request

### Campos
`approval_id` · `approval_type` (`discount` | `non_standard_terms` | `contract_terms` | `exception_win`) · `object_type` · `object_id` · `requester_user_id` · `approver_user_id?` · `threshold_ref` (clave config, no valor hardcode obligatorio) · `reason` · `status` · `decision_note?` · `requested_at` · `decided_at?` · `expires_at?`

### Estados
`pending` · `approved` · `rejected` · `canceled` · `expired`

---

## Separación de funciones

| Acción | Rol |
|--------|-----|
| Solicitar | `sales_agent` |
| Aprobar/rechazar dentro de política | `sales_manager` |
| Vista auditoría | `auditor`, `platform_admin` |
| Auto-aprobación sobre umbral | **Prohibida** |
| Aprobación por org owner cliente | **Prohibida** |

`platform_finance` (015): **DEFERRED** para términos no estándar si HUM004 = incluir.

---

## Reglas

| ID | Regla |
|----|-------|
| BR-APR-01 | Objeto bloqueado para `sent`/`accept` mientras approval `pending` cuando type lo exige |
| BR-APR-02 | Toda decisión auditada |
| BR-APR-03 | Requester ≠ approver efectivo (misma persona prohibida si supera umbral) |
| BR-APR-04 | Umbrales exactos = config / decisión humana |
| BR-APR-05 | Expiración automática → `expired`; requiere nuevo request |

---

## Inbox UI
Lista `pending` para sales_manager.
