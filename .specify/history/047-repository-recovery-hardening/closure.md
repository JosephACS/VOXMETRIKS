# Closure — 047 Repository Recovery & Hardening

**Estado:** cerrado  
**Commit de referencia documental:** `d2f6a27f` (y commits posteriores de music-core, enterprise residual, UX/infra)

## Decisiones retenidas
- Recuperación **selectiva** de paquetes 033–044 (no dirty-tree completo).
- Preservar 046.
- Reportes org-scoped con `X-Organization-Id`.
- Unified Music Search: **diferido durante el recovery inicial 047**; el **núcleo** quedó **implementado posteriormente** por la reconciliación music-core (`/tracks/music-search`, adopt, repair-source, frontend local → YouTube → adopt, pruebas asociadas). Pendiente: smoke con API key/proveedor real y alcance avanzado no aprobado.
- Household profiles sin filtrar PII; prepare-switch sin sesión/token.
- Checkout antiguo solo lectura durante la recuperación.

## Inventario / seguridad / validación
- Gates backend/frontend documentados en la fase (pytest + `npm test` / build).
- Org isolation: 400 sin header; 403 org ajena; 200 con membresía.
- Hardening posterior: refunds org-scoped, reset atómico, compose canónico, higiene runtime.

## Resultado
Worktree de recuperación consolidado en `main @ d2f6a27f` y siguientes.  
**No hay feature Spec Kit activa de implementación**; el directorio 047 se conserva solo por compatibilidad de herramientas.
