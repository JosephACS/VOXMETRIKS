# Accepted debt — Spec 017

| Deuda | Impacto | Riesgo | Mitigación | Responsable futuro | Spec futura | Razón aceptación |
|-------|---------|--------|------------|-------------------|-------------|------------------|
| Playwright E2E CRM absent | No browser golden-path proof | Medio | Integration + unit cover critical paths | QA / next CRM hardening | 017 follow-up or ops | Config only; same class as 016 |
| FE bundle budget >550 kB | Perf warning | Bajo | Preexisting; not introduced solely by CRM | Frontend | tech debt | Historical |
| Residual CRM rows in warehouse | Local noise counts | Bajo | Documented; no delete policy | Ops | cleanup script optional | No destructive cleanup authorized |
| Idempotency-Key not fully persisted (org create debt carries) | Retry edge cases | Bajo | slug/unique conversion guards | Backend | 016/017 follow-up | Inherited / partial |
| platform_finance OUT | Non-standard terms approval limited to sales_manager | Bajo | Documented deferred | Product | future | Explicit decision #5 |
| Discount threshold config optional | Any discount>0 needs approval | Bajo | Config key `crm_discount_approval_threshold` | Sales ops | — | Conservative default |
| Consolidated use_case modules vs many tiny files | Traceability granularity | Bajo | Evidence maps modules to US | Eng | — | Speed/DRY |
| DuckDB academic limits | Not SaaS transactional | Medio | Known constitution limit | Architecture | PG migration future | Inherited |
