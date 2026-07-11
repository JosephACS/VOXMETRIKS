# Role and Permission Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Scope de permisos:** **platform** (no org-scoped 016).  
**Separación:** roles org-cliente (`owner`, `administrator`, …) **no** implican CRM.

---

## Actores internos (RBAC plataforma)

| Rol | Responsabilidad |
|-----|-----------------|
| `sales_agent` | Prospectos, opps, actividades, cotizaciones, avance, solicitar aprobaciones, iniciar convert (si policy) |
| `sales_manager` | Todo agent + approve/reject + reopen + coaching |
| `platform_admin` | Break-glass / configuración; audit view; no sustituye sales día a día |
| `auditor` | Solo lectura auditoría / evidencias |

### Participantes externos (no RBAC)
prospect contact · decision maker · authorized signatory — viven como `crm_contact`, no como roles de plataforma.

### Diferidos
`platform_finance` (015 términos no estándar) — HUM004.

---

## Permisos (códigos)

| Permiso | Descripción |
|---------|-------------|
| `crm.prospect.view` | Ver prospectos |
| `crm.prospect.create` | Crear |
| `crm.prospect.update` | Actualizar / transiciones no convert |
| `crm.opportunity.view` | Ver pipeline |
| `crm.opportunity.create` | Crear |
| `crm.opportunity.update` | Avanzar stages |
| `crm.opportunity.close` | won/lost/canceled |
| `crm.activity.manage` | CRUD lógico actividades |
| `quotation.create` | Crear draft/version |
| `quotation.update` | Editar draft |
| `quotation.send` | Enviar |
| `quotation.approve` | Aprobar cotización/descuento (manager) |
| `contract.create` | Crear contrato |
| `contract.approve` | Aprobar contrato |
| `contract.accept` | Registrar aceptación académica |
| `customer.convert` | Ejecutar conversión |
| `crm.audit.view` | Ver auditoría CRM |

---

## Matriz (diseño)

| Permiso | agent | manager | platform_admin | auditor |
|---------|:-----:|:-------:|:--------------:|:-------:|
| crm.prospect.view | ✓ | ✓ | ✓ | ✓ (si audit path) |
| crm.prospect.create/update | ✓ | ✓ | ✓ | — |
| crm.opportunity.* | ✓ | ✓ | ✓ | view vía audit |
| crm.opportunity.close | ✓ | ✓ | ✓ | — |
| crm.activity.manage | ✓ | ✓ | ✓ | — |
| quotation.create/update/send | ✓ | ✓ | ✓ | — |
| quotation.approve | — | ✓ | ✓* | — |
| contract.create | ✓ | ✓ | ✓ | — |
| contract.approve | — | ✓ | ✓* | — |
| contract.accept | ✓ | ✓ | ✓ | — |
| customer.convert | ✓** | ✓ | ✓* | — |
| crm.audit.view | — | ✓ | ✓ | ✓ |

\* break-glass auditado · \*\* policy puede restringir convert a manager (HUM).

---

## Reglas

| ID | Regla |
|----|-------|
| BR-RBAC-01 | Org roles 016 no otorgan permisos CRM |
| BR-RBAC-02 | Frontend no es fuente de verdad |
| BR-RBAC-03 | Lista/detalle CRM filtra platform scope; post-link org_id es dato, no ACL cliente |
| BR-RBAC-04 | Assign de roles sales = proceso plataforma (fuera o al borde de 017) |

---

## Relación con 016

Conversión llama a Organizations con identidad del actor sales (service/use case), no “impersona” owner cliente sin audit.
