# Specs operativas — Voxmetriks

Índice canónico de la capa SDD (specs **001–011**). Constitución: [`.specify/memory/constitution.md`](../.specify/memory/constitution.md).

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

Cada carpeta incluye `spec.md`, `checklists/requirements.md` y, en 001–007, `traceability-appendix.md`.

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
| [TRACEABILITY-COVERAGE-REPORT.md](TRACEABILITY-COVERAGE-REPORT.md) | 2.0.0 | Cobertura cadena 001–011 |
| [DOCUMENT-COVERAGE-REPORT.md](DOCUMENT-COVERAGE-REPORT.md) | 2.0.0 | Cobertura documental + histórico 001–006 |
| [OPERATIVE-COMPLETENESS-AUDIT.md](OPERATIVE-COMPLETENESS-AUDIT.md) | 2.0.0 | ICO ~88 %; addendum post 008–011 |
| [SPEC-008-011-EVIDENCE-AUDIT.md](SPEC-008-011-EVIDENCE-AUDIT.md) | 1.0.0 | Evidencia código pre-spec 008–011 |
| [OPERATIVE-GAP-ANALYSIS.md](OPERATIVE-GAP-ANALYSIS.md) | 1.0.0 | **Archivado** — brechas pre-008 |

---

## UML

Diagramas derivados de estas specs: [`docs/uml/`](../docs/uml/).

---

## Arranque del proyecto

No duplicar instrucciones aquí — ver [`docs/QUICKSTART.md`](../docs/QUICKSTART.md).
