# Spec 016 — Deferred decisions

| Decisión | Motivo | Spec/tema futuro | Riesgo | Condición |
|----------|--------|------------------|--------|-----------|
| Reopen org closed → active | No regla de negocio cerrada | orgs follow-up | orgs zombie | decisión humana + dual control |
| NotificationPort email real | Infra no comprobada | platform notifications | invites solo académicos | provider + config |
| Custom org roles | Complejidad RBAC | orgs RBAC+ | proliferación permisos | tras catálogo fijo estable |
| Password hashing upgrade | Deuda seguridad global | security-auth | hashes débiles | spec seguridad |
| Tenancy en playlists/favoritos | Personal mode | futura | datos mixtos | tras adopción org |
| PostgreSQL / RLS nativo | Fuera 016 | platform data | límites DuckDB | decisión arquitectura |
| Numeración/feature.json activo | Proceso | al autorizar impl | confusión feature activa | autorización humana |
| Retiro modo sin org | 015 diferido | identity/orgs follow-up | dual mode | métricas adopción |
| Google login + org invites | Edge identity | identity | email mismatch OAuth | pruebas dedicadas |
