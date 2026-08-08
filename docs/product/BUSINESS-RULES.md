# Business rules (transversales)

| Regla | Estado |
|-------|--------|
| Tenant isolation vía organización + header | Implementado |
| RBAC / permisos de módulo | Implementado (parcial; sin métrica de cobertura inventada) |
| Una moneda por factura / allocations coherentes | Diseñado → parcial en billing |
| Idempotencia de reembolsos por org | Implementado |
| Reset password atómico; intentos defensivos persistentes | Implementado |
| Artist invitation token no en query string | Implementado (046) |
| Household profiles sin filtrar email/login hints en listados | Implementado |
| No afirmar pasarela/compliance/streaming licenciado | Vigente |

Parámetros comerciales (precio, trial days por mercado, fees): **diferidos**.
