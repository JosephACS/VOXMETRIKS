# Audit and Security — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Principios

1. Deny by default.  
2. Autorización **solo backend**.  
3. CRM platform-scoped ≠ org ACL cliente.  
4. Sin PAN/CVV.  
5. Sin afirmaciones de cumplimiento legal / e-sign certificada.  
6. Tokens/secretos nunca en audit ni responses de listados.  
7. Misma honestidad DuckDB que 016 (aislamiento por aplicación).

---

## Controles

| Amenaza | Control |
|---------|---------|
| Org member lee CRM | 403 sin permiso platform CRM |
| IDOR prospect/opportunity | ownership checks + 404/403 |
| Self-approve descuento | BR-APR-03 |
| Double conversion | unique + idempotency |
| Mutar quotation sent | 409 |
| Accept expired | 410 |
| Bypass admin técnico | BR-SEC-CRM-02 |
| PII export masivo | audit.view restringido; rate limits futuros |
| Injection en activity body | sanitize store/display |

---

## Auditoría obligatoria

Create/update/transition de: prospect, opportunity, quotation send/accept, approval decide, contract accept, conversion.  
Campos: actor_user_id, action, entity_type, entity_id, at, request_id?, sanitized diff.

---

## Datos sensibles

| Dato | Tratamiento |
|------|-------------|
| email/phone contact | PII; mínimo necesario |
| acceptance_evidence | retención comercial |
| terms_snapshot | no secretos de pago |
| linked invite tokens | nunca; solo invitation_id |

---

## Tests de seguridad (diseño)

Ver `test-strategy.md` § security.
