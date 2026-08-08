# Spec 047 — Repository Recovery, Runtime Completeness & Product Hardening

## Resumen

Recuperar e integrar selectivamente backends y wiring de Specs 033–044 que existen en el checkout principal sucio pero no en `origin/main` (post-046), sin degradar Artist Spaces (045/046), sin monetización nueva, y sin promover a `main` en esta fase.

## Objetivos

1. **Recuperación forense**: inventario del working tree sucio vs `origin/main@7cba24d0`.
2. **Runtime demostrable**: demo local sin depender obligatoriamente de PocketBase; fixtures idempotentes.
3. **Completar APIs huérfanas**: Workpanel, reportes simples/complejos, listening, profile security, module access, sync catalog.
4. **Correcciones web**: 404/403 engañosos, chrome Platform Admin, perfiles, Artist Search empty state.
5. **Limpieza repo**: `.gitignore`, artefactos generados, estructura canónica `apps/frontend`.
6. **Preservar 046**: routers Artist Space, memberships, invitations (token en body), `spaceKind === 'artist'`.

## Fuera de alcance

- Monetización / planes de artista / Spec 048.
- Merge o FF a `main` (requiere revisión externa).
- Copiar screenshots/PDFs/temporales automáticamente.
- Borrar el checkout principal ni sus 574 cambios.

## Actores afectados

Listener, Platform Admin, Engineer (Data Ops), Artist Space members, Staff (Workpanel/Reports).

## Criterios de aceptación

- `/api/v1/workpanel` no 404.
- `/api/v1/reports/simple|complex/catalog` no 404.
- Routers 046 presentes en `app.main`.
- Demo seed canónico documentado e idempotente.
- Tests 046 30/30 + suites recuperadas; FE spaces 32/32; `ng build` PASS.
- Sin staging/commit/push hasta instrucción explícita posterior.
