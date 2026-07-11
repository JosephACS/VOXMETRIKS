# Spec 014 — Closure report (Phase G)

**Fecha:** 2026-07-11  
**Spec:** `automation/specs/014-repository-stabilization-domain-foundation/`  
**Estado oficial de la spec:** **CLOSED_WITH_ACCEPTED_DEBT** (cierre documental 2026-07-11).  
Ver también: `final-validation.md`, `accepted-debt.md`, `spec-closure.md`.

---

## 1. Alcance completado

| Fase | Resultado |
|------|-----------|
| A Baseline | Completada (evidencia previa) |
| B Constitución | Completada |
| C Frontend packages | Completada (URLs intactas; re-exports `features/`) |
| D1 API facade + auth | Completada |
| D2 Package-by-domain | Completada (`identity`/`catalog`/`engagement` + shims) |
| E ELT canónico | Completada (`analytics/elt` + adaptador; gap de paridad documentado) |
| F Playback docs | Completada (sin migración de código) |
| G Cleanup + validación | Completada (este reporte) |

**No incluido (fuera de alcance / aplazado):** dominios CRM/billing/orgs; migración playback-core; eliminación de shims; reescritura completa de TRACEABILITY-MASTER; workers ELT async.

---

## 2. Archivos principales afectados (014)

- Backend: `packages/{identity,catalog,engagement}`, shims `users`/`streaming`, `api/route_policy`, auth D1, `etl/canonical_adapter`, `pipeline/orchestrator`
- Frontend: consolidación analytics packages; rutas públicas sin cambio
- Docs: `README.md`, `docs/QUICKSTART.md`, `docs/architecture/elt.md`, `docs/playback/SPEC_014_PHASE_F_DECISION.md`, overview, índice docs
- Tooling: `infrastructure/Makefile`, `.github/workflows/ci.yml`, `.gitignore`
- OpenSpec: `tasks.md`, `checklist.md`, este reporte

---

## 3. Pruebas (Phase G — 2026-07-11)

| Suite | Resultado |
|-------|-----------|
| Backend `pytest -q` | **168 passed**, 0 failed |
| Uvicorn `:8017` + `/health` | **200 healthy** |
| Smoke auth/API V1/V2 | login 200, tracks 200, overview 200, anon overview **401**, V2 overview 200, playlists 200 |
| Canonical ELT script resolve | **True** (sin full rebuild) |
| `validate_warehouse.py` | OK (facts/aggs; DB ~261 MB) |
| Frontend `npm test` | **59 passed** |
| Frontend `npm run lint` | **0 errors**, 13 warnings |
| Frontend `ng build` (dev) | **PASS** |
| Audio + ELT adapter tests | **PASS** |
| Docker | **NOT_VERIFIED** (no disponible en entorno) |
| Playwright | **NOT_VERIFIED** (`node_modules` ausente) |
| Smoke interactivo playback | **NOT_VERIFIED** |

### Row counts warehouse (lectura; sin delta injustificado)

| Tabla | Count |
|-------|------:|
| dim_track | 89740 |
| dim_artista | 31429 |
| dim_album | 46154 |
| fact_streaming | 585000 |
| app_user | 5 |
| app_session | 242 |
| app_playlist | 4 |
| app_favorite | 7 |
| Tablas totales | 42 |

---

## 4. Gates finales

| Gate | Resultado | Notas |
|------|-----------|-------|
| G1 Working tree sin generados versionados | **PASS** (política) | `.gitignore` ampliado (zips specs, logs `_*.txt`); no se ejecutó `git status` |
| G2 Backend inicia | **PASS** | Uvicorn + TestClient |
| G3 `/health` OK | **PASS** | `healthy` |
| G4 Backend tests | **PASS** | 168 |
| G5 Frontend tests | **PASS** | 59 |
| G6 Frontend build | **PASS** | |
| G7 Lint sin errores | **PASS** | 13 warnings aceptados |
| G8 Contratos API | **PASS** | Smoke V1/V2 |
| G9 Rutas sensibles | **PASS** | 401 anónimo overview (D1) |
| G10 Warehouse válido | **PASS** | validate_warehouse |
| G11 Esquema/conteos | **PASS** | Sin cambios injustificados en G |
| G12 ELT canónico documentado | **PASS** | docs + Makefile |
| G13 Playback sin regresión (pruebas disponibles) | **PASS** (parcial) | Unit/audio; no smoke manual |
| G14 README/QUICKSTART alineados | **PASS** | Actualizados en G |
| G15 Specs/checklist | **PASS** | Actualizados |

---

## 5. Deudas aceptadas

1. Shims `packages/users` y `packages/streaming` (consumidores) — no retirar en 014.
2. `app/etl` runtime ≠ paridad total con `analytics/elt`.
3. TRACEABILITY-MASTER: rutas históricas; mapeo documentado, sin reescritura de 248 filas.
4. UI playback: inyección mixta MusicPlayerService / PlayerController.
5. Playback-core V2 no migrado.
6. CI ampliado a suite completa — no ejecutado en GitHub Actions en este entorno.
7. `pb_data` sigue versionado a propósito (QUICKSTART); no se añadió a `.gitignore`.

---

## 6. Elementos aplazados

- Spec de migración playback-core.
- Spec de dominios empresariales (CRM, billing, orgs, …).
- Worker/cola para ELT full fuera del boot API.
- Regeneración automática de matriz de trazabilidad.
- Instalación Playwright + e2e en CI.
- Validación Docker Compose en máquina de desarrollo.

---

## 7. Riesgos

- Confundir `make etl` con `make pipeline`.
- `RUN_ETL_ON_BOOT=full` puede bloquear arranque.
- Warnings de budget Angular / eslint `any` en YouTube engine.
- Documentación histórica en `docs/archive` y auditorías antiguas pueden contradecir el estado 014 (no reescritas).

---

## 8. Recomendación de cierre

**CLOSED_WITH_ACCEPTED_DEBT** (formalizado en `spec-closure.md`).

La estabilización técnica de 014 está evidenciada (A–G). Quedan deudas explícitas y gates de infra/e2e en **NOT_VERIFIED**. Spec 015 no iniciada. Commits pendientes = proceso manual del usuario.
