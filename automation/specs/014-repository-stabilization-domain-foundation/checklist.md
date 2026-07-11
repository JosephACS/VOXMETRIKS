# Requirements Checklist: Spec 014 — Repository Stabilization Domain Foundation

**Purpose**: Gate de aceptación antes/durante/después de la ejecución autorizada  
**Created**: 2026-07-11  
**Updated**: 2026-07-11 (post-revisión externa)  
**Feature**: [spec.md](./spec.md) · [plan.md](./plan.md) · [tasks.md](./tasks.md)

## Gobierno

- [ ] CHK001 Spec número **014** confirmado (siguiente tras 013)
- [ ] CHK002 Carpeta contiene spec/plan/tasks/checklist
- [ ] CHK003 Specs 001–013 no movidas
- [ ] CHK004 `.specify` = tooling; specs en `automation/specs/`
- [ ] CHK005 Ningún dominio empresarial vacío creado
- [ ] CHK006 Sin cambios funcionales intencionales excepto seguridad documentada

## Constitución (Fase B)

- [ ] CHK007 Monorepo real documentado
- [ ] CHK008 Ubicación real de specs documentada
- [ ] CHK009 Package-by-domain técnico vs empresarial aclarado
- [ ] CHK010 Estado real de audio documentado (YouTube + Audius con evidencia + demo)
- [ ] CHK011 Prohibición de módulos vacíos + OpenSpec antes de cambios estructurales
- [ ] CHK012 Naming honesto AI / Enterprise / RC
- [ ] CHK013 Principio **negocio → objetivos → procesos → actores → casos de uso → reglas → datos → backend → frontend → reportes → IA**

## Frontend (Fase C)

- [ ] CHK014 Paths de `app.routes.ts` sin cambio de URL pública
- [ ] CHK015 `features/` absorbido o residual documentado
- [ ] CHK016 lint / unit / build ejecutados; resultados reales
- [ ] CHK017 Playwright ejecutado o no disponible documentado
- [ ] CHK018 Player: cero cambios de código; MusicPlayerService intacto

## Backend (Fase D)

- [ ] CHK019 Packages identity/catalog/engagement/analytics/ai (o shims)
- [ ] CHK020 Fachada canónica `/api/v1` conserva contratos FE; implementación por endpoint vía consumidores/pruebas/seguridad (no “Packages V1 = toda la API”)
- [ ] CHK021 Enterprise V1/V2 como adaptadores mientras haya consumidores
- [ ] CHK022 Auth documentada en rutas sensibles; 401/403 sin permiso
- [ ] CHK023 Contratos `/api/v1` usados por FE operativos
- [ ] CHK024 pytest ejecutado; sin regresiones nuevas no documentadas

## ELT (Fase E)

- [ ] CHK025 `analytics/elt` declarado canónico
- [ ] CHK026 `apps/backend/app/etl` **no eliminado**
- [ ] CHK027 Adaptador solo si paridad demostrable; si no, gap documentado
- [ ] CHK028 `RUN_ETL_ON_BOOT` preservado
- [ ] CHK029 Esquema DuckDB sin cambios
- [ ] CHK030 Row counts antes/después de: `dim_track`, `dim_artista`, `dim_album`, `fact_streaming`, `app_user`, `app_session`, `app_playlist`, `app_favorite` — OK o justificados

## Playback (Fase F)

- [ ] CHK031 Dirección futura documentada (SoT = playback-core post-014)
- [ ] CHK032 Cero integración de playback-core en 014
- [ ] CHK033 MusicPlayerService se mantiene
- [ ] CHK034 Solo commit de docs si aplica; T037/T040 no autorizan código de player
- [ ] CHK035 Pruebas playback existentes ejecutadas; reproducción básica OK (G7)

## Limpieza (Fase G)

- [ ] CHK036 Shims/legacy retirados solo con cero consumidores
- [ ] CHK037 README / QUICKSTART / Docker / Makefile / CI actualizados si aplicó
- [ ] CHK038 Trazabilidad actualizada o deuda explícita
- [ ] CHK039 Validación final sin resultados inventados

## Gates G1–G9

- [ ] CHK040 G1 Backend inicia
- [ ] CHK041 G2 Frontend carga y permite login
- [ ] CHK042 G3 Endpoints consumidos mantienen contrato
- [ ] CHK043 G4 Rutas sensibles → 401/403 sin permiso
- [ ] CHK044 G5 Esquema DuckDB no cambia
- [ ] CHK045 G6 Row counts críticos OK o justificados
- [ ] CHK046 G7 Reproducción básica funcional
- [ ] CHK047 G8 No se versionan secretos ni archivos generados
- [ ] CHK048 G9 Cada fase tiene rollback por commit

## Baseline / stop (Fase A)

- [ ] CHK049 `git status` revisado; cambios ajenos mostrados y no stash/reset/commit sin autorización
- [ ] CHK050 Si regresión no resoluble → fase detenida y revertida

## Notes

- Marcar `[x]` solo con evidencia.
- Este checklist no sustituye la auditoría de dominio; la referencia.
