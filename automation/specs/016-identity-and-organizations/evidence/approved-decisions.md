# Spec 016 — Approved design decisions

**Fecha:** 2026-07-11  
**Autoridad:** criterios conservadores autorizados en validación de diseño

| ID | Decisión |
|----|----------|
| A | Organización activa = preferencia persistida **revalidada** en cada request; precedencia path > header > preferencia; conflicto path/header → 400 |
| B | Usuario sin org = modo personal/demo temporal; endpoints empresariales requieren contexto |
| C | Roles personalizados fuera de v1; catálogo fijo |
| D | Invitaciones sin email real = modo académico; token una vez; no afirmar envío; NotificationPort futuro |
| E | Eliminación = estados lógicos; no borrado físico de auditables |
| F | Primer owner = creador de la organización |
| G | Multi-organización desde la primera implementación |
| H | Slug único globalmente en v1 |
| I | Org demo solo seed explícito (`is_demo`), nunca automática |
| J | DuckDB válido académicamente; aislamiento por aplicación + pruebas |
