# Pricing Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING  
**Sin precios definitivos. Sin FX.**

---

## plan_price

### Campos
`plan_price_id` · `plan_id` · `currency` (ISO) · `billing_period` (`month`|`year`|configurable enum) · `amount` (decimal ≥ 0) · `status` (`active`|`retired`) · `valid_from?` · `valid_to?` · timestamps

### Reglas
| ID | Regla |
|----|-------|
| BR-PRICE-01 | Unique lógico (plan_id, currency, billing_period, status=active) — una tarifa activa por slice |
| BR-PRICE-02 | amount configurable; seed demo etiquetado `is_demo` si aplica |
| BR-PRICE-03 | No conversión FX; subscription hereda currency del price elegido |
| BR-PRICE-04 | Retire price: nuevas subs no lo usan; existentes conservan snapshot en subscription |
| BR-PRICE-05 | amount=0 permitido solo con política explícita (trial/freemium) y auditoría |

### Snapshot
Al crear subscription: copiar `plan_price_id`, `currency`, `billing_period`, `amount` a campos snapshot de subscription (anti-drift silencioso).

### Honestidad
Listar precios en UI como **configurables / demo** hasta política comercial humana.
