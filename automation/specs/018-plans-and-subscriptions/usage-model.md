# Usage Model — Spec 018

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## usage_record

`usage_id` · `organization_id` · `subscription_id` · `feature_code` · `quantity` · `recorded_at` · `period_start` · `period_end` · `source` (`system`|`manual`|`import`) · `idempotency_key?`

### Reglas
| ID | Regla |
|----|-------|
| BR-USE-01 | Append-oriented; correcciones con adjustment record (no delete físico) |
| BR-USE-02 | Comparar quantity vs entitlement.limit_value |
| BR-USE-03 | Over-limit → señal para access `limited` según política (HUM008) — no cobro automático |
| BR-USE-04 | Idempotency_key para ingest |
| BR-USE-05 | No confundir usage musical warehouse (`fact_*`) con usage SaaS entitlements |

### KPI
usage vs limit (ops); sin inventar series.
