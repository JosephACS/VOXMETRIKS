# Checklist de verificación pre-entrega (Bloque 5)

**Versión:** 1.0.0  
**Fecha:** 2026-06-19  
**Propósito:** Verificación exhaustiva **antes** del PDF final (Bloque 6).  
**Artefacto maestro:** [`TRACEABILITY-MASTER.md`](TRACEABILITY-MASTER.md) v2.0.0

---

## 1. Resumen de verificación

| Área | Estado | Evidencia |
|------|--------|-----------|
| Matriz trazabilidad 001–011 | ✅ | 248 filas, 0 errores `generate_traceability.py` |
| Columna Impl + Evidencia | ✅ | 240 Implementado, 8 Parcial, 0 Pendiente |
| Specs redactadas | ✅ | 11/11 `specs/*/spec.md` |
| Tests API mínimos | ✅ | 12 passed (`backend/tests/test_api.py`) |
| UML derivado | ✅ | 4 diagramas `docs/uml/**/*.puml` |
| Quickstart único | ✅ | `README.md` → `docs/01-introduction/quickstart.md` |
| Informes de cobertura | ✅ | Actualizados v2.0 (este bloque) |
| Delimitaciones 003/010, 006/011, 007/008 | ✅ | Tablas en specs + §4 abajo |
| Deuda conocida documentada | ⚠️ | 8 FR Parcial + riesgos seguridad (§6) |

**Veredicto Bloque 5:** **Listo para armar PDF** con deudas explícitas en anexo (no bloqueantes para entrega ingenieril demo).

---

## 2. Verificaciones automatizadas (ejecutadas)

### 2.1 Trazabilidad

```bash
python specs/_tools/generate_traceability.py
```

| Resultado | Valor |
|-----------|------:|
| Filas | 248 |
| HUs únicas | 61 |
| CUs únicos | 98 |
| FRs únicos | 221 |
| Errores cadena CU→HU→FR→CA | 0 |

Meta: [`specs/_tools/traceability-meta.json`](_tools/traceability-meta.json)

### 2.2 Tests backend

```bash
cd backend && pytest tests/test_api.py -q
```

| Resultado | Valor |
|-----------|------:|
| Tests | 12 passed |
| Cobertura funcional | health, login, playlists, favorites |

### 2.3 Inventario specs

| Spec | `spec.md` | Checklist | Filas matriz |
|------|-----------|-----------|-------------:|
| 001 | ✅ | ✅ | 22 |
| 002 | ✅ | ✅ | 20 |
| 003 | ✅ | ✅ | 22 |
| 004 | ✅ | ✅ | 22 |
| 005 | ✅ | ✅ | 22 |
| 006 | ✅ | ✅ | 18 |
| 007 | ✅ | ✅ | 36 |
| 008 | ✅ | ✅ | 26 |
| 009 | ✅ | ✅ | 20 |
| 010 | ✅ | ✅ | 21 |
| 011 | ✅ | ✅ | 19 |
| **Total** | **11/11** | **11/11** | **248** |

---

## 3. Coherencia documental

| Documento | Versión | Alcance | Estado |
|-----------|---------|---------|--------|
| `TRACEABILITY-MASTER.md` | 2.0.0 | 001–011 + Impl | ✅ Canónico |
| `_archive/audits/` | — | Informes puntuales 2026-06 | ✅ Archivados |
| `README.md` (raíz) | — | Entrada única | ✅ |
| `docs/01-introduction/quickstart.md` | — | Arranque | ✅ |
| `docs/02-architecture/structure.md` | — | Mapa del repo | ✅ |
| `specs/README.md` | — | Índice specs | ✅ |
| `.env.example` | — | Ruta DuckDB | ✅ `data/warehouse/voxmetrik.duckdb` |

### 3.1 Entrada única de arranque

| Archivo | Estado |
|---------|--------|
| `quickstart.md` (raíz) | Redirige a `docs/01-introduction/quickstart.md` |
| `backend/README.md` | Estructura API; arranque en `docs/01-introduction/quickstart.md` |
| `docs/archive/SETUP_LEGACY.md` | Setup legacy archivado |

---

## 4. Delimitaciones obligatorias (sin duplicar FR)

| Par | Spec A (consumo) | Spec B (operaciones) | Regla |
|-----|------------------|----------------------|-------|
| **003 ↔ 010** | Lectura catálogo, browse, búsqueda | CRUD steward POST/PUT/DELETE | 003 Out of Scope steward; 010 owns mutaciones |
| **006 ↔ 011** | Tab settings health (CU-ST05) | Contrato `/health`, root metadata | 006 = UX consumidor; 011 = contrato API y ops |
| **007 ↔ 008** | BI consumo (`/stats`, trending) | Pipeline UI, synthetic, loads, warehouse | 007 Out of Scope pipeline/synthetic |
| **004 ↔ 007** | Home hub escucha (CU-H01) | KPI rail analítico (CU-AN08) | Embed documentado; no redefinir FR-R* |
| **006 ↔ 008** | Tabs engineer estáticos settings | ELT pipeline `/elt-pipeline` | 008 owns orquestación; 006 solo prefs UI |
| **001 ↔ 006** | API perfil/prefs | UX `/users`, `/settings` | Tabla delimitación en spec 006 |

Referencias: `010-catalog-steward/spec.md`, `011-health-operations/spec.md`, `007-operational-analytics-dashboards/spec.md` §Out of Scope.

---

## 5. FR con Impl = Parcial (8 filas)

| FR | Spec | Brecha documentada | Evidencia |
|----|------|--------------------|-----------|
| FR-014 | 001 | Guard redirect incompleto en rutas edge | `app.routes.ts` |
| FR-C12 | 003 | Paginación artistas parcial en UI | `artists.component.html` |
| FR-S03 | 003 | Filtro búsqueda backend limitado | `tracks.py` |
| FR-C13 | 003 | Acciones contextuales track-row parciales | `track-row.component.ts` |
| FR-AN26 | 007 | KPI rail dashboard layout parcial | `dashboard-layout.component.ts` |
| FR-PM18 | 008 | Tab warehouse settings estático | `settings.component.ts` |
| FR-PM19 | 008 | Tab pipeline prefs solo localStorage | `ui-preferences.service.ts` |
| FR-CS15 | 010 | Auth steward ausente (P11) | `artists.py` |

Fuente: [`_tools/implementation_evidence.py`](_tools/implementation_evidence.py)

---

## 6. Riesgos conocidos (incluir en PDF / anexo)

| ID | Riesgo | Severidad | Acción post-entrega |
|----|--------|-----------|---------------------|
| R-SEC-01 | CRUD catálogo sin auth backend | Alta | Spec 010 FR-CS15; hardening |
| R-SEC-02 | Endpoints engineer/synthetic sin RBAC BE | Alta | Alinear FR-015 con 008 |
| R-SEC-03 | Passwords SHA-256 demo | Media | Fuera alcance demo |
| R-SEC-04 | CORS `*` | Media | Producción |
| R-PROD-01 | Pipeline ELT UI simulado vs CLI real | Media | Documentado en spec 008 |
| R-PROD-02 | No existe `/api/info` | Baja | Spec 011 usa `/` y `/health` |
| R-GOV-01 | Specs estado Draft | Media | Ratificación formal |
| R-GOV-02 | Constitución OT-08…10 no ratificados | Media | Anexo constitucional |

---

## 7. UML y diagramas

| Archivo | Contenido | Verificado |
|---------|-----------|:----------:|
| `docs/uml/use-cases/01-use-cases.puml` | CU por spec 001–011 | ✅ |
| `docs/uml/components/02-components.puml` | PKG-01…07 FE/BE | ✅ |
| `docs/uml/architecture/03-architecture.puml` | Docker, Medallion, volúmenes | ✅ |
| `docs/uml/elt/04-elt-flow.puml` | CLI vs UI simulada + synthetic | ✅ |
| `docs/uml/README.md` | Instrucciones render PlantUML | ✅ |

Render opcional pre-PDF: PlantUML local o [plantuml.com](https://www.plantuml.com/plantuml).

---

## 8. API — contratos verificados vs docs

| Endpoint | Documentado en | Respuesta real (tests/código) |
|----------|----------------|-------------------------------|
| `GET /health` | 011 | `{status, database, tables, version}` |
| `GET /` | 011 | `{app, version, docs, health}` — **no** `{status: running}` |
| Prefijo API | Constitución | `/api/v1` |
| Login demo | QUICKSTART | `demo`/`demo123`, `admin`/`admin123` |

**No documentar:** `GET /api/info` (no existe).

---

## 9. Checklist Bloque 6 — PDF final

Marcar al generar el entregable:

- [ ] Portada (proyecto, versión matriz 2.0.0, fecha)
- [ ] Índice
- [ ] Resumen ejecutivo (ICO ~88 %, 248 filas, 11 specs)
- [ ] Constitución — extracto §12 trazabilidad
- [ ] Matriz resumida o enlace TRACEABILITY-MASTER (248 filas)
- [ ] Resumen por spec 001–011 (1 página c/u o tabla consolidada)
- [ ] Tabla 8 FR Parcial + plan mitigación
- [ ] Diagramas UML (PNG/SVG exportados)
- [ ] Quickstart condensado (5 pasos)
- [ ] Resultados tests (12 passed)
- [ ] Anexo riesgos §6
- [ ] Anexo delimitaciones §4

---

## 10. Comandos de re-verificación rápida

```bash
# Desde raíz del repo
python specs/_tools/generate_traceability.py
cd backend && pytest tests/test_api.py -q
```

Si ambos pasan sin error, el estado documental coincide con este checklist.

---

**Elaborado por:** Bloque 5 — unificación y verificación pre-PDF  
**Siguiente paso:** Bloque 6 — compilación PDF según §9
