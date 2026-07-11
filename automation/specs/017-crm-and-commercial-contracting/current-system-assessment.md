# Current System Assessment — Spec 017

**Status**: Diseñado (assessment) · **IMPLEMENTATION_PENDING**  
**Fecha**: 2026-07-11  
**Método:** revisión documental 015/016 + existencia de paquetes (sin afirmar CRM en código).

---

## Qué existe hoy

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Identity (login/sesión bearer) | **Implementado** | 016 + `packages/identity` |
| Organizations / members / invites / RBAC org | **Implementado** | 016 CLOSED_WITH_ACCEPTED_DEBT |
| Active organization context | **Implementado** | 016 |
| Audit org-scoped | **Implementado** (parcial deudas 016) | 016 |
| Analytics / streaming / player | **Parcial/implementado** | specs previas; **no** CRM |
| CRM / prospects / quotations | **No implementado** | sin package `crm` |
| Commercial contract | **No implementado** | solo diseño 015 |
| Subscriptions / billing / payments | **Diseñado** (015) · no código | OUT de 017 |

---

## Contradicciones / tensiones con el sistema actual

1. **015 opportunity states** (`open|negotiation|won|lost`) vs **017** (`open|qualified|proposal|negotiation|won|lost|canceled`) — 017 **refina**; al implementar, actualizar trazabilidad 015 como superseded-by-017 en esos puntos.  
2. **015 quotation states** simples vs **017** versionado + `pending_approval|superseded|canceled`.  
3. **015 contract** usa `signed`/`active`; **017** usa aceptación académica (`accepted` / `active_handoff`) sin afirmar e-sign.  
4. **015** separa dominios `crm` y `contracts`; **017** es **una capacidad** de implementación que cubre ambos hasta conversión.  
5. **016** permite crear org a cualquier autenticado; conversión CRM debe usar el mismo dominio pero con **política de origen sales** (no duplicar create fuera de Organizations).  
6. **Enterprise analytics** actual ≠ pipeline comercial — no reutilizar endpoints enterprise como CRM.  
7. **Roles técnicos** `admin`/`engineer` (identity) ≠ `sales_*` / `platform_admin` comercial — no bypass CRM.  
8. **DuckDB** no aísla nativamente — mismo patrón 016 (WHERE + tests).  
9. **Email real** no existe — actividades `email_reference` solo metadatos.  
10. **Planes**: no hay catálogo `plan` implementado — `plan_code` en cotización es **referencia conceptual**.

---

## Reutilización obligatoria

| Componente | Uso en 017 |
|------------|------------|
| `app_user` / sesión | Actores sales autenticados |
| Organizations create/link/invite | Conversión |
| Permission deny-by-default | Extender catálogo permisos CRM (plataforma) |
| Audit patterns 016 | Eventos CRM sin secretos |

## No reutilizar

| Anti-patrón | Por qué |
|-------------|---------|
| Tablas warehouse `dim_*` como CRM | Ownership incorrecto |
| Org-member permissions para CRM | Scope distinto |
| Invoice/payment mocks como “aceptación” | Billing OUT |
| Auto-crear `app_user` desde contact email | FR contactos |

---

## Baseline honesto

```text
CRM = DESIGN_APPROVED / IMPLEMENTATION_PENDING
Organizations = IMPLEMENTATION_COMPLETE (016)
Subscriptions/Billing = DESIGN_APPROVED (015) / OUT 017
```
