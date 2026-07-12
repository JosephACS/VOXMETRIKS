# Role and Permission Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Actores

### Organización (016 roles)
| Rol | Subscription |
|-----|----------------|
| `owner` | Full subscription manage + cancel |
| `billing_manager` | Manage subscription/trial/addons; view usage |
| `administrator` | View subscription; limited manage (policy) |
| `finance` | View (prep billing); no catalog publish |
| `viewer` / others | View if `subscription.view` granted |

### Plataforma
| Rol | Catalog / break-glass |
|-----|------------------------|
| `platform_admin` | Publish/retire plans & prices |
| `auditor` | Audit view |
| `platform_finance` | **DEFERRED** (billing) — lectura catálogo opcional HUM006 |

CRM `sales_*` **no** gestionan subscriptions de clientes (pueden ver plan catalog público si se permite).

---

## Permisos propuestos

### Platform catalog
`plan.view` · `plan.create` · `plan.publish` · `plan.retire` · `plan_price.manage` · `feature.manage` · `addon.manage`

### Organization-scoped
`subscription.view` · `subscription.create` · `subscription.change` · `subscription.cancel` · `subscription.reactivate` · `usage.view` · `usage.record` (system) · `entitlement.view`

---

## Matriz (diseño)

| Permiso | owner | billing_manager | administrator | platform_admin | auditor |
|---------|:-----:|:---------------:|:-------------:|:--------------:|:-------:|
| subscription.view | ✓ | ✓ | ✓ | ✓* | ✓* |
| subscription.create/change/cancel | ✓ | ✓ | △ | ✓* | — |
| plan.publish | — | — | — | ✓ | — |
| audit | △ | △ | — | ✓ | ✓ |

\* platform justificado/auditado · △ configurable

## Reglas
BR-RBAC-SUB-01 Org roles no publican catálogo global.  
BR-RBAC-SUB-02 Frontend no es autoridad.  
BR-RBAC-SUB-03 CRM roles ≠ subscription manage.
