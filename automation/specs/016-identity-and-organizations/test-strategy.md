# Test Strategy — Spec 016

**Status**: DESIGN_APPROVED — IMPLEMENTATION_PENDING

## Unitarias
Estados org/member/invite/context · último owner · token hash one-time · matriz permisos · precedencia contexto · slug único · idempotencia create

## Integración
Repos filter organization_id (no filtrar en Python post-hoc) · tx create org · accept invite · audit append · login usuario existente sin org

## Seguridad
cross-tenant read/update · suspended 403 · ID arbitrario · sin org en enterprise · platform elevated no silencioso · support reason+expiry

## API
contratos HTTP 400/401/403/404/409/410/422 · paginación · errores negocio

## Frontend
selector · none state · permission hide · invite academic token once · navigation guards

## E2E
crear org → invitar → aceptar → asignar rol → cambiar contexto → verificar acceso → intento Org B → auditoría

## Trazabilidad CA → prueba

Cada US1–US7 y FR-001–011 tiene al menos una prueba futura asociada (mapa en traceability.md).
