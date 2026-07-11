# Feature Specification: Entregables de Defensa Académica

**Feature Branch**: `013-academic-defense-deliverables`  
**Feature Directory**: `specs/013-academic-defense-deliverables/`  
**Created**: 2026-07-03  
**Status**: Implemented — documentación verificada contra código  
**Input**: Fase final del proyecto: documentación enterprise, arquitectura, base de datos DBML, casos de uso por paquetes, top 10 CU detallados, guion y recorrido de defensa. Sin nuevas funcionalidades de producto.

**Prerrequisitos:** Specs 001–012 implementadas; warehouse DuckDB con 48 tablas; trazabilidad `TRACEABILITY-MASTER.md` v2.0.0.

**Evidencia base:** Carpeta externa `../voxmetriks-entregas/`; `docs/` del repo producto; código en `backend/`, `frontend/`, `elt/`.

---

## Contexto Empresarial

La evaluación académica prioriza: (1) diseño de base de datos Medallion, (2) casos de uso agrupados por paquetes, (3) implementación trazable de cada caso de uso. Esta spec formaliza los **entregables de defensa** sin modificar lógica de negocio.

---

## Objetivo

Producir documentación enterprise **100 % derivada del código real**:

1. Inventario completo del sistema (módulos, APIs, tablas, componentes).
2. Modelo DBML (`warehouse.dbml`) con las 48 tablas RAW/DIM/FACT/AGG/APP/CTL.
3. Documento técnico profesional (13 secciones).
4. Catálogo de casos de uso por PKG + detalle de 10 CU seleccionados.
5. Guion de defensa (10–15 min) y recorrido de demostración.
6. Organización en `voxmetriks-entregas/` con subcarpetas 01–06.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Estudiante presenta arquitectura y BD (Priority: P1)

Como presentador, quiero documentación técnica y DBML verificables para explicar el diseño dimensional al tribunal.

**Independent Test:** Importar `02-BaseDatos/warehouse.dbml` en dbdiagram.io sin errores; todas las tablas visibles.

**Acceptance Scenarios**:

1. **Given** el warehouse DuckDB cargado, **When** reviso `warehouse.dbml`, **Then** contiene 48 tablas con columnas, PKs y relaciones lógicas deducibles del ELT.
2. **Given** `DOCUMENTO_TECNICO.md`, **When** leo secciones 1–13, **Then** cada afirmación corresponde a archivos reales (backend, frontend, elt).

---

### User Story 2 - Estudiante demuestra casos de uso (Priority: P1)

Como presentador, quiero 10 casos de uso de negocio con trazabilidad código para la defensa oral.

**Independent Test:** Cada CU en `DETALLE_TOP10_CASOS_DE_USO.md` referencia endpoints, tablas y pantallas existentes.

**Acceptance Scenarios**:

1. **Given** el catálogo PKG-01..07, **When** leo nombres de CU, **Then** son procesos de negocio (ej. "Autenticar usuario"), no botones UI.
2. **Given** los 10 CU seleccionados, **When** sigo el recorrido demo, **Then** cubren identidad, catálogo, escucha, biblioteca, recomendaciones, analítica y datos.

---

### User Story 3 - Tribunal valida inventario (Priority: P2)

Como evaluador, quiero inventario verificable de APIs, rutas Angular y tablas.

**Independent Test:** `INVENTARIO_SISTEMA.md` coincide con conteos de grep/código (93 endpoints, 46 componentes, 48 tablas).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-AD01**: MUST existir `voxmetriks-entregas/02-BaseDatos/warehouse.dbml` con 48 tablas completas.
- **FR-AD02**: MUST existir `01-Arquitectura/DOCUMENTO_TECNICO.md` con estructura de 13 secciones.
- **FR-AD03**: MUST existir catálogo CU por paquete en `03-CasosDeUso/CATALOGO_CASOS_DE_USO.md`.
- **FR-AD04**: MUST existir detalle de 10 CU en `03-CasosDeUso/DETALLE_TOP10_CASOS_DE_USO.md`.
- **FR-AD05**: MUST existir guion y recorrido en `05-GuionDefensa/`.
- **FR-AD06**: MUST existir inventario en `06-Anexos/INVENTARIO_SISTEMA.md`.
- **FR-AD07**: MUST copiarse docs del proyecto a `06-Anexos/docs-proyecto/` sin modificar código producto.
- **FR-AD08**: MUST organizarse entregables en subcarpetas 01–06.
- **FR-AD09**: MUST registrarse esta spec como 013 en `specs/README.md`.
- **FR-AD10**: MUST NOT introducir cambios funcionales en backend/frontend/elt.

### Non-Functional Requirements

- **NFR-AD01**: Documentación en español profesional, tono enterprise.
- **NFR-AD02**: Relaciones DBML solo lógicas/deducibles; sin FK físicas inventadas en DuckDB.
- **NFR-AD03**: DBML compatible dbdiagram.io sin post-procesado.

---

## Success Criteria *(mandatory)*

1. Tribunal puede visualizar el modelo completo en dbdiagram.io en menos de 2 minutos.
2. Los 10 CU demostrables en vivo en 5–7 minutos siguiendo `RECORRIDO_DEMOSTRACION.md`.
3. Guion oral completable en 10–15 minutos.
4. 100 % de tablas warehouse documentadas en DBML.
5. Cero discrepancias entre conteos inventario y código fuente auditado.

---

## Key Entities

| Entidad | Ubicación entregables |
|---------|----------------------|
| Modelo warehouse | `02-BaseDatos/warehouse.dbml` |
| Casos de uso | `03-CasosDeUso/` |
| Arquitectura | `01-Arquitectura/DOCUMENTO_TECNICO.md` |
| Diagramas UML | `04-Diagramas/uml-rendered/` |
| Guion defensa | `05-GuionDefensa/` |
| Anexos / docs proyecto | `06-Anexos/` |

---

## Assumptions

- Warehouse ETL ya ejecutado para demo en vivo.
- Credenciales demo: `demo/demo123`, engineer: `admin/admin123`.
- Spec Kit permanece en repo producto; entregas académicas en carpeta hermana.

---

## Out of Scope

- Nuevas features de producto.
- Refactors de código.
- Diagramas Mermaid/PlantUML para BD (solo DBML).
- Modificación de lógica ETL o API.

---

## Trazabilidad entregables

| FR | Evidencia |
|----|-----------|
| FR-AD01 | `voxmetriks-entregas/02-BaseDatos/warehouse.dbml` |
| FR-AD02 | `voxmetriks-entregas/01-Arquitectura/DOCUMENTO_TECNICO.md` |
| FR-AD03–04 | `voxmetriks-entregas/03-CasosDeUso/` |
| FR-AD05 | `voxmetriks-entregas/05-GuionDefensa/` |
| FR-AD06–07 | `voxmetriks-entregas/06-Anexos/` |
| FR-AD09 | `specs/README.md` §013 |

Ver también: `traceability-appendix.md` en esta carpeta.
