# Migration and Compatibility — Spec 016

**Status**: DESIGN_APPROVED

## Conservar

app_user · app_session · logout/login existentes · no invalidar sesiones por schema add  

## Usuarios actuales sin org (estrategia)

Los usuarios existentes (p. ej. demo/admin y cuentas locales) **permanecen sin organization** hasta que:

1. creen una org, o  
2. acepten una invitación, o  
3. un seed **explícito** de desarrollo cree org demo marcada `is_demo=true`.

**MUST NOT** inventar organizaciones “reales” ni backfill automático para “los cinco usuarios”.

## Seeds demo

Solo ENV development + flag; marcar is_demo; documentado en runbook futuro.

## Rollback

Desactivar feature flag rutas org · dejar tablas · sesiones intactas.

## Warehouse / catálogo analítico

**No alterar** dim_*/fact_* en 016.
