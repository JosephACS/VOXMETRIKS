# Accepted debt — Spec 016

| Deuda | Impacto | Riesgo | Mitigación | Responsable futuro | Spec futura | Razón de aceptación |
|-------|---------|--------|------------|--------------------|-------------|---------------------|
| Playwright E2E Organizations ausente | Sin golden-path browser | Medio | API/security pytest cubren flujo lógico | QA / FE | 017+ tooling e2e | Config existe; 0 specs; gates BE/FE PASS |
| Bundle budget (644.42 > 550 kB) | Warning build | Bajo | Documentar; optimizar FE en spec posterior | FE | 014 residual / FE perf | Preexistente; build OK |
| home.component.css budget | Warning build | Bajo | Idem | FE | FE polish | Preexistente; fuera de alcance 016 |
| Deny-audit incompleto (no `result=denied` en cada 403/404) | Menos telemetría seguridad | Medio | Success audits + security tests | Backend | hardening org | Ruido/coste académico |
| Elevated platform grants (reason/expiry/persist) | No ops de plataforma vía HTTP | Bajo (deny-by-default) | Solo `platform_admin`/`security_admin` UC; sin ruta HTTP | Backend | platform elevation | Evitar bypass temporal |
| Idempotency-Key HTTP no persistida | Retries pueden duplicar invites | Medio | Slug-deterministic create org | Backend | reliability | Deuda I2 documentada |
| DuckDB concurrencia / ART índices | Límites académicos | Medio | TX + re-read accept; docs | Data | Postgres migration (015) | DuckDB no es SaaS definitivo |
| Warehouse residual orgs (10) de sesiones previas | Datos no “limpios” | Bajo | No borrar reales; tests en DB temporal | Ops | cleanup policy | Honestidad; identity=5 estable |
| Members UI muestra `user_id` sin email join | UX incompleta | Bajo | Contrato membership sin email | FE+BE | org UX polish | Contrato I3 suficiente para 016 |
| api-contracts: revoke perm texto vs `invitation.revoke` | Doc drift menor | Bajo | Código + seeds son autoridad | Docs | doc sync | Comportamiento correcto |
| Password SHA-256 identity | Seguridad auth heredada | Medio | Fuera de 016 | Identity | auth hardening | Preexistente; no ampliar alcance |
| Roles catalog billing_manager sin módulo billing | Confusión semántica | Bajo | Comentarios catalog; perms limitados | Product | billing spec | Prep RBAC; módulo OUT_OF_SCOPE |
