# Business Rules — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Heredadas 015 (vigentes)

| ID | Regla |
|----|-------|
| BR-ORG-05 | Mora no cambia organization.status |
| BR-SUB-01 | Features ⊆ entitlements activos |
| BR-SUB-02 | Trial no factura salvo política |
| BR-SUB-03 | Cancel end-of-term vs immediate |
| BR-SUB-04 | Todo cambio → subscription_change |
| BR-SUB-05 | Una billing_currency por subscription |
| BR-SUB-06 | No FX v1 |
| BR-SUB-07 | No leer tablas internas billing |
| BR-SUB-08 | past_due → access limited/blocked vía orquestación |

## Ampladas 018

Ver modelos: BR-PLAN-* · BR-PRICE-* · BR-ENT-* · BR-SUB-018-* · BR-TRIAL-* · BR-CHG-* · BR-ADD-* · BR-USE-* · BR-REN-* · BR-ACC-*

## Dinero / honestidad

| ID | Regla |
|----|-------|
| BR-MON-018-01 | No afirmar subscription “pagada” sin PaymentSettled |
| BR-MON-018-02 | Precios = configurables; no tarifas oficiales inventadas |
| BR-MON-018-03 | No PAN/CVV |
| BR-HON-018-01 | Seed demo planes etiquetados |
| BR-HON-018-02 | activation_source obligatorio en create |

## Seguridad

| ID | Regla |
|----|-------|
| BR-SEC-SUB-01 | Deny by default feature checks |
| BR-SEC-SUB-02 | Org isolation por organization_id |
| BR-SEC-SUB-03 | Platform catalog perms ≠ org billing_manager |
| BR-SEC-SUB-04 | No bypass por identity admin/engineer |
