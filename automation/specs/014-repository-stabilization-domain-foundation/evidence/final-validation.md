# Spec 014 — Final validation

**Fecha:** 2026-07-11  
**Fuente primaria:** `closure-report.md` (Phase G) + fases A–F revisadas  
**Alcance:** Solo consolidación de evidencia documental (sin re-ejecutar suites en este cierre).

---

## Resumen de validación

| Área | Resultado | Clasificación |
|------|-----------|---------------|
| Backend pytest | 168 passed, 0 failed (G) | **Completado** |
| Backend `/health` | 200 `healthy` (Uvicorn + TestClient) | **Completado** |
| Smoke auth + API V1/V2 | login/tracks/overview/playlists OK; overview anónimo 401 | **Completado** |
| Warehouse validate | OK; 42 tablas; row counts estables | **Completado** |
| Frontend unit tests | 59 passed | **Completado** |
| Frontend lint | 0 errors, 13 warnings | **Completado** (warnings = deuda) |
| Frontend build | PASS (dev); warnings de budget posibles | **Completado** / **Parcial** (budget) |
| Adaptador ELT canónico | Script resoluble; sin full rebuild en validación | **Completado** |
| Auth D1 (401/403) | Cubierto por tests + smoke | **Completado** |
| Contratos FE `/api/v1` | Conservados (401/403 auth OK) | **Completado** |
| Docker Compose | No ejecutado con éxito en entorno de cierre | **No verificado** |
| Playwright e2e | `node_modules` ausente | **No verificado** |
| Login SPA en browser | No smoke interactivo | **No verificado** |
| Playback interactivo (G7 manual) | No ejecutado | **No verificado** |
| CI en GitHub Actions | Workflow actualizado; run remoto no comprobado aquí | **No verificado** |
| `git status` / commits | Usuario gestiona Git; agente sin comandos Git | **Diferido** (proceso) |

---

## Gates (cierre)

| ID | Gate | Estado |
|----|------|--------|
| G1 | Política anti-generados / `.gitignore` | **PASS** (sin `git status`) |
| G2 | Backend inicia | **PASS** |
| G3 | `/health` | **PASS** |
| G4 | Backend tests | **PASS** |
| G5 | Frontend tests | **PASS** |
| G6 | Frontend build | **PASS** |
| G7 | Lint sin errores | **PASS** (warnings aceptados) |
| G8 | Contratos API | **PASS** |
| G9 | Rutas sensibles | **PASS** |
| G10 | Warehouse válido | **PASS** |
| G11 | Conteos/esquema | **PASS** |
| G12 | ELT canónico documentado | **PASS** |
| G13 | Playback (pruebas disponibles) | **PASS** parcial |
| G14 | README/QUICKSTART | **PASS** |
| G15 | Specs/checklist | **PASS** (este cierre) |
| — | Docker | **NOT_VERIFIED** |
| — | Playwright | **NOT_VERIFIED** |
| — | FE login browser | **NOT_VERIFIED** |

---

## Fuera de alcance (no fallos)

- Dominios empresariales (CRM, billing, orgs, …)
- Migración de código a `playback-core`
- Eliminación de `app/etl` o shims con consumidores
- Cambio de esquema DuckDB
- Spec 015

Ver también: `accepted-debt.md`, `spec-closure.md`.
