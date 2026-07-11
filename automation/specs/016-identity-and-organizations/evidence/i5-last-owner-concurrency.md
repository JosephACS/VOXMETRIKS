# I5 — Last owner & concurrency

**Status**: COMPLETE

## Guard

`ensure_organization_has_active_owner_after_mutation` + SQL `count_active_owners`.

Bloquea leave / remove / suspend / revoke owner cuando dejaría 0 owners activos.

## Concurrencia académica (DuckDB)

- Accept re-lee invitation dentro de TX.
- DuckDB single-writer: contención serializada; no se simula true parallel writers.
- Límite documentado: aislamiento académico suficiente; no claim de serialización distribuida.

## Pruebas

`test_last_owner_guards`, API `test_last_owner_leave_blocked`.
