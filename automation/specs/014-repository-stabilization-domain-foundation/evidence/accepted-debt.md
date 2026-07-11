# Spec 014 — Accepted debt

**Fecha:** 2026-07-11  
**Estado:** Deudas **aceptadas** al cierre documental. No bloquean `CLOSED_WITH_ACCEPTED_DEBT`.

---

## Infraestructura y herramientas

| Deuda | Detalle | Clasificación |
|-------|---------|---------------|
| Docker no validado | `docker version` / compose no verificados con éxito en el entorno de ejecución de 014 | **No verificado** → aceptado |
| Playwright no disponible | `automation/playwright/node_modules` ausente; e2e no corridos | **No verificado** → aceptado |
| CI remoto | Workflow local actualizado (pytest completo, lint, Python 3.12); run en GitHub Actions no comprobado aquí | **No verificado** → aceptado |
| Warnings de bundle | Build Angular puede emitir avisos de budget; no se modificó código para ocultarlos | **Parcial** / aceptado |
| ESLint warnings | 13 warnings (p. ej. `any` en YouTube engine); 0 errors | Aceptado |

---

## Adaptadores y legacy

| Deuda | Detalle | Clasificación |
|-------|---------|---------------|
| Adapters legacy FE | Re-exports `features/*.component.ts` hacia packages | **Diferido** (retirar cuando cero consumidores) |
| Adapters legacy BE | `packages/users` → `identity`; `packages/streaming` → catalog/engagement (+ audio en streaming) | **Diferido** |
| Enterprise V1 + V2 + packages | Superficies coexistentes bajo fachada `/api/v1` / adaptadores V2 | **Diferido** — migración API legacy futura |
| `app/services` / repositories enterprise | Capa paralela a packages; no reorg estética en 014 | **Diferido** |

---

## ELT

| Deuda | Detalle | Clasificación |
|-------|---------|---------------|
| Retiro futuro del ELT backend | `apps/backend/app/etl` conservado (runtime refresh + tests); gap de paridad con `analytics/elt` documentado | **Diferido** |
| Full rebuild en boot | `RUN_ETL_ON_BOOT=full` existe pero no es el default; worker/cola = spec futura | **Diferido** / fuera de alcance 014 |
| TRACEABILITY rutas ELT | Matriz aún cita paths históricos; mapeo en cabecera | **Diferido** |

---

## Playback

| Deuda | Detalle | Clasificación |
|-------|---------|---------------|
| Migración futura de playback-core | SoT activo = `MusicPlayerService`; core = dirección futura / parcial | **Diferido** (spec propia) |
| UI mixta controller vs service | Consumidores duales | **Parcial** |
| Smoke interactivo G7 | No ejecutado | **No verificado** |

---

## Datos y plataforma

| Deuda | Detalle | Clasificación |
|-------|---------|---------------|
| Límites de DuckDB | Warehouse single-file; no multi-tenant Redis; no escala “millones de usuarios” (fuera de alcance 014) | **Fuera de alcance** / aceptado como límite de producto |
| Regeneración TRACEABILITY-MASTER | 248 filas históricas sin rewrite masivo | **Diferido** |

---

## Límites legales del audio

| Deuda | Detalle | Clasificación |
|-------|---------|---------------|
| Audio YouTube / Audius / demo | Reproducción **no** implica derechos comerciales de catálogo Spotify ni CDN propio; demo WAV es fallback UX | **Fuera de alcance** / límite legal documentado (constitución + Fase F) |
| No scrapear / no afirmar licencia | Producto = analytics + catálogo gobernado + demo; no servicio de streaming licenciado | Aceptado |

---

## Migración futura de API legacy

| Deuda | Detalle | Clasificación |
|-------|---------|---------------|
| Consolidar envelopes V1 enterprise vs V2 plano | Coexistencia intencional en 014 | **Diferido** |
| Retirar rutas duplicadas cuando cero consumidores | Solo tras grep + tests | **Diferido** |

---

## Commits manuales (proceso)

T022, T030, T035, T040, T046 y commits A/B quedan a cargo del usuario (Source Control). No son fallos de implementación; son **diferidos de proceso**.

---

## No son deudas de 014 (fuera de alcance explícito)

- Dominios: organizations, crm, subscriptions, billing, campaigns, customer_success, support, compliance, catalog_rights
- Spec 015
- Cambios de esquema DuckDB
- IA “avanzada” / modelos locales presentados como SOTA
