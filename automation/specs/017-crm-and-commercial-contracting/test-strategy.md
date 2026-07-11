# Test Strategy (diseño) — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
Ninguna suite CRM existe aún.

---

## Capas futuras

| Capa | Contenido |
|------|-----------|
| Unit dominio | transiciones estado, version immutability, currency, threshold gate |
| Repository | CRUD + unique conversion + pagination |
| Use cases | quotation send/accept/expire; approval; convert saga |
| API | permisos 401/403; platform scope; idempotency |
| Security | org-cliente vs sales; IDOR; no admin bypass |
| Frontend unit | guards CRM; board transitions; read-only sent quote |
| E2E Playwright | golden path sales-assisted (diseñado) |
| Compat | identity + orgs smoke post-CRM |

---

## Casos obligatorios

1. Platform scope: prospect sin organization_id propietario.  
2. Permisos sales_agent vs sales_manager (approve).  
3. Estados opportunity ilegales → 422.  
4. Quotation versionada: edit sent → 409; new version OK.  
5. Approval required sobre umbral; self-approve forbidden.  
6. Expiración quotation bloquea accept.  
7. Contract accept con evidence; sin e-sign claim.  
8. Duplicate conversion → 409.  
9. create_org vía Organizations: owner presente; no huérfana.  
10. link_existing requiere confirmación / no silent wrong link.  
11. Contacto sin user → invitation 016.  
12. Auditoría en accept/convert.  
13. Idempotency-Key convert.  
14. Usuario org-cliente sin CRM perm → 403 en `/crm/*`.  
15. No side effect subscription/invoice tables (assert ausencia o no calls).

---

## Golden path E2E (diseñado)

login sales_agent → create prospect → contact → opportunity → activity → quotation draft → (approval si discount) → send → accept quote → contract → accept → convert → org exists → login org owner (invite) → CRM still denied for that owner → audit entries visibles a auditor.

Cross: sales_agent B no lee opportunity de A si policy owner-only (si se adopta); mínimo: sin permiso → 403.

---

## KPIs en pruebas

No assert valores de negocio inventados; solo que agregaciones N/D o 0 honestos con fixtures controlados.
