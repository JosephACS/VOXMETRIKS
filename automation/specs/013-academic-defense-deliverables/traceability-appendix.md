# Trazabilidad — Spec 013 Entregables Defensa Académica

**Versión:** 1.0.0 · **Fecha:** 2026-07-03

## Mapa FR → Entregable

| ID | Requisito | Archivo entregable | Verificación |
|----|-----------|-------------------|--------------|
| FR-AD01 | DBML 48 tablas | `voxmetriks-entregas/02-BaseDatos/warehouse.dbml` | Import dbdiagram.io |
| FR-AD02 | Doc técnico 13 § | `voxmetriks-entregas/01-Arquitectura/DOCUMENTO_TECNICO.md` | Revisión manual |
| FR-AD03 | Catálogo CU | `voxmetriks-entregas/03-CasosDeUso/CATALOGO_CASOS_DE_USO.md` | PKG-01..07 |
| FR-AD04 | Top 10 CU | `voxmetriks-entregas/03-CasosDeUso/DETALLE_TOP10_CASOS_DE_USO.md` | Trazabilidad endpoints |
| FR-AD05 | Guion + demo | `voxmetriks-entregas/05-GuionDefensa/` | Timing 10–15 min |
| FR-AD06 | Inventario | `voxmetriks-entregas/06-Anexos/INVENTARIO_SISTEMA.md` | Conteos código |
| FR-AD07 | Docs proyecto | `voxmetriks-entregas/06-Anexos/docs-proyecto/` | Copia docs/ |
| FR-AD08 | Estructura 01–06 | `voxmetriks-entregas/README.md` | Índice |
| FR-AD09 | Registro spec | `specs/README.md` §013 | Este archivo |
| FR-AD10 | Sin cambios código | diff vacío backend/frontend | Git status |

## Evaluación 09 (Construcción del Software)

Entregables académicos video YouTube — **solo en carpeta externa** `../voxmetriks-entregas/`:

| Documento | Ruta entregas |
|-----------|---------------|
| Word Eval 09 | `EVALUACION_09_CONSTRUCCION_SOFTWARE.docx` |
| 10 CU + navegación | `03-CasosDeUso/EVALUACION_09_10_CASOS_DE_USO.md` |
| PlantUML × 11 | `04-Diagramas/plantuml/eval09/` |
| Captura BD | `04-Diagramas/capturas/BD_48_tablas_dbdiagram.png` |

## Top 10 CU → Spec origen

| CU | Nombre | Spec | PKG |
|----|--------|------|-----|
| CU-02 | Autenticar usuario | 001 | PKG-01 |
| CU-C | Explorar catálogo | 003 | PKG-02 |
| CU-S | Buscar contenido | 003 | PKG-02 |
| CU-R | Gestionar reproducción | 004 | PKG-03 |
| CU-F | Administrar favoritos | 002 | PKG-02 |
| CU-P | Administrar playlists | 002 | PKG-02 |
| CU-RC | Recomendaciones personalizadas | 005 | PKG-04 |
| CU-AN | Analítica operacional | 007 | PKG-06 |
| CU-PM | Monitorear pipeline ELT | 008 | PKG-07 |
| CU-DE | Explorar warehouse | 009 | PKG-07 |

## Relación con TRACEABILITY-MASTER

Spec 013 no añade filas CU→FR nuevas; consolida evidencia documental de specs 001–012 ya implementadas.
