# Requirements Checklist: Spec 014 — Repository Stabilization Domain Foundation

**Purpose**: Gate de aceptación  
**Created**: 2026-07-11  
**Closed**: 2026-07-11 — **CLOSED_WITH_ACCEPTED_DEBT**  
**Feature**: [spec.md](./spec.md) · [plan.md](./plan.md) · [tasks.md](./tasks.md) · [evidence/spec-closure.md](./evidence/spec-closure.md)

## Gobierno

- [x] CHK001 Spec número **014** confirmado
- [x] CHK002 Carpeta contiene spec/plan/tasks/checklist + evidence/
- [x] CHK003 Specs 001–013 no movidas
- [x] CHK004 `.specify` = tooling; specs en `automation/specs/`
- [x] CHK005 Ningún dominio empresarial vacío creado
- [x] CHK006 Sin cambios funcionales intencionales excepto seguridad documentada (D1)

## Constitución (Fase B)

- [x] CHK007 Monorepo real documentado
- [x] CHK008 Ubicación real de specs documentada
- [x] CHK009 Package-by-domain técnico vs empresarial aclarado
- [x] CHK010 Estado real de audio documentado (YouTube + Audius + demo)
- [x] CHK011 Prohibición de módulos vacíos + OpenSpec antes de cambios estructurales
- [x] CHK012 Naming honesto AI / Enterprise / RC
- [x] CHK013 Principio **negocio → objetivos → procesos → actores → casos de uso → reglas → datos → backend → frontend → reportes → IA**

## Frontend (Fase C)

- [x] CHK014 Paths de `app.routes.ts` sin cambio de URL pública
- [x] CHK015 `features/` absorbido; residual = re-exports
- [x] CHK016 lint / unit / build ejecutados (59 PASS; 0 err / 13 warn; build PASS)
- [x] CHK017 Playwright no disponible documentado
- [x] CHK018 Player: cero cambios de código en C/F
- [x] CHK018b Null metrics → “No disponible”

## Backend (Fase D)

- [x] CHK019 Packages identity/catalog/engagement/analytics/ai (+ shims)
- [x] CHK020 Fachada `/api/v1` canónica por endpoint
- [x] CHK021 Enterprise V1/V2 como adaptadores
- [x] CHK022 Auth 401/403
- [x] CHK023 Contratos FE operativos
- [x] CHK024 pytest sin regresiones no documentadas (168 PASS al cierre G)

## ELT (Fase E)

- [x] CHK025 `analytics/elt` canónico
- [x] CHK026 `app/etl` no eliminado
- [x] CHK027 Gap de paridad documentado
- [x] CHK028 `RUN_ETL_ON_BOOT` documentado
- [x] CHK029 Esquema DuckDB sin cambios
- [x] CHK030 Row counts OK

## Playback (Fase F)

- [x] CHK031 Dirección futura documentada
- [x] CHK032 Sin integración playback-core como reemplazo
- [x] CHK033 MusicPlayerService se mantiene
- [x] CHK034 Solo docs de player en F
- [x] CHK035 Unit/audio PASS; G7 interactivo **NOT_VERIFIED**

## Limpieza (Fase G)

- [x] CHK036 Shims conservados (tienen consumidores)
- [x] CHK037 Docs/CI/gitignore actualizados; Docker **NOT_VERIFIED**
- [x] CHK038 Trazabilidad: deuda + mapeo
- [x] CHK039 Validación final documentada

## Gates

- [x] CHK040 Backend inicia
- [ ] CHK041 Frontend login browser — **NOT_VERIFIED**
- [x] CHK042 Contratos API
- [x] CHK043 Auth sensible
- [x] CHK044 Esquema DuckDB
- [x] CHK045 Row counts
- [x] CHK046 Playback parcial (automatizado PASS; interactivo N/V)
- [x] CHK047 Política secretos/generados (gitignore); git status agente omitido
- [ ] CHK048 Rollback por commit — **diferido** (usuario / Source Control)

## Baseline

- [ ] CHK049 `git status` por agente — **omitido** (regla permanente usuario)
- [x] CHK050 Sin regresión no resoluble bloqueante

## Cierre

- [x] `evidence/final-validation.md`
- [x] `evidence/accepted-debt.md`
- [x] `evidence/spec-closure.md`
- **Estado:** CLOSED_WITH_ACCEPTED_DEBT
- Spec 015: **no iniciada**

## Notes

- Marcar `[x]` solo con evidencia.
- No afirmar CRM/billing/orgs ni playback-core completo.
