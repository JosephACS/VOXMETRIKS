# Specs operativas — Voxmetriks

Índice canónico de la capa SDD (specs **001–013**). Constitución: [`.specify/memory/constitution.md`](../.specify/memory/constitution.md).

---

## Specs por dominio

| # | Carpeta | Objetivo táctico | Paquete |
|---|---------|------------------|---------|
| 001 | [user-identity-access](001-user-identity-access/spec.md) | OT-01 Identidad | PKG-01 |
| 002 | [personal-music-library](002-personal-music-library/spec.md) | OT-02 Biblioteca | PKG-02 |
| 003 | [catalog-discovery](003-catalog-discovery/spec.md) | OT-03 Catálogo | PKG-02 |
| 004 | [listening-experience](004-listening-experience/spec.md) | OT-04 Escucha | PKG-03 |
| 005 | [personalized-discovery](005-personalized-discovery/spec.md) | OT-05 Descubrimiento | PKG-04 |
| 006 | [account-self-service](006-account-self-service/spec.md) | OT-06 Autogestión | PKG-05 |
| 007 | [operational-analytics-dashboards](007-operational-analytics-dashboards/spec.md) | OT-07 Analítica BI | PKG-06 |
| 008 | [pipeline-monitoring](008-pipeline-monitoring/spec.md) | OT-08 Pipeline ELT | PKG-07 |
| 009 | [data-explorer](009-data-explorer/spec.md) | OT-09 Explorer | PKG-07 |
| 010 | [catalog-steward](010-catalog-steward/spec.md) | OT-09 Steward CRUD | PKG-02 |
| 011 | [health-operations](011-health-operations/spec.md) | OT-10 Health / ops | PKG-05 |
| 012 | [auto-quality-gates](012-auto-quality-gates/spec.md) | OT-11 Calidad / CI | Transversal |
| 013 | [academic-defense-deliverables](013-academic-defense-deliverables/spec.md) | OT-12 Defensa académica | Documentación |

Cada carpeta incluye `spec.md`, `checklists/requirements.md` y, en 001–007, **012** y **013**, apéndice de trazabilidad.

**Entregables defensa (013):** carpeta externa [`../voxmetriks-entregas`](../voxmetriks-entregas) — DBML, CU, guion, inventario.

---

## Trazabilidad e implementación

| Documento | Versión | Contenido |
|-----------|---------|-----------|
| [TRACEABILITY-MASTER.md](TRACEABILITY-MASTER.md) | **2.0.0** | 248 filas — CU→FR→Impl→Evidencia |
| [_tools/implementation_evidence.py](_tools/implementation_evidence.py) | — | Mapa FR → código |
| [_tools/generate_traceability.py](_tools/generate_traceability.py) | — | Regenera matriz maestra |

Regenerar matriz:

```bash
python specs/_tools/generate_traceability.py
```

---

## Auditorías y cobertura

| Informe | Versión | Notas |
|---------|---------|-------|
| [**DELIVERY-VERIFICATION-CHECKLIST.md**](DELIVERY-VERIFICATION-CHECKLIST.md) | **1.0.0** | **Pre-PDF Bloque 5 — verificaciones ejecutadas** |
| [_archive/audits/](_archive/audits/README.md) | — | Informes puntuales archivados (2026-06) |

Estado vigente: [TRACEABILITY-MASTER.md](TRACEABILITY-MASTER.md).

---

## UML

Diagramas derivados de estas specs: [`docs/uml/`](../docs/uml/).

---

## Arranque del proyecto

No duplicar instrucciones aquí — ver [`docs/01-introduction/quickstart.md`](../docs/01-introduction/quickstart.md).
