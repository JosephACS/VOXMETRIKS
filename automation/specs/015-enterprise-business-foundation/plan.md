# Implementation Plan: Enterprise Business Foundation

**Branch**: `015-enterprise-business-foundation` *(propuesta)* | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

**Status**: **CLOSED_WITH_DEFERRED_DECISIONS** (2026-07-11) — plan documental cerrado; implementación = specs futuras.

**Input**: Fundación empresarial B2B SaaS de VOXMETRIKS.

---

## Summary

La spec 015 define el modelo de negocio, objetivos, procesos, roles, estados, cobro, dominios, datos conceptuales, KPIs y mapa de specs futuras.  
**No** modifica `apps/`, DuckDB, APIs ni reproducción. La “implementación” de 015 es **completar y validar artefactos documentales** + checklist de coherencia.

Specs posteriores (sin números definitivos) implementarán dominios según `future-specification-map.md`.

---

## Technical Context

| Campo | Valor |
|-------|-------|
| **Language/Version** | N/A (documentación Markdown / Spec Kit) |
| **Primary Dependencies** | Spec Kit / OpenSpec; Constitución v1.1.0; spec 014 cerrada |
| **Storage** | **Sin cambios**. Modelo conceptual solo; DuckDB intacto |
| **Testing** | Revisión humana + checklist; pruebas de código = **futuro** |
| **Target Platform** | Documentación en `automation/specs/015-.../` |
| **Project Type** | Business foundation / SDD artifacts |
| **Performance Goals** | N/A |
| **Constraints** | No código; no feature.json; no Constitución; no Git por agente |
| **Scale/Scope** | ~25 artefactos de modelo empresarial |

---

## Constitution Check

| Gate | Resultado |
|------|-----------|
| Specs en `automation/specs/` | **PASS** |
| No crear dominios vacíos en código | **PASS** (solo docs) |
| Naming honesto (diseñado ≠ implementado) | **Obligatorio** |
| Cadena negocio → evidencia | **PASS** (principio ampliado en 015) |
| Audio no como streaming comercial | **PASS** |
| Enmienda constitucional por redefinición de negocio principal | **Diferida** — decisión humana (ver contradicciones) |

---

## Project Structure

### Documentation (this feature)

```text
automation/specs/015-enterprise-business-foundation/
├── spec.md
├── plan.md                 # este archivo
├── tasks.md                # tareas documentales / gates
├── checklist.md
├── business-model.md
├── strategic-model.md
├── tactical-model.md
├── operational-model.md
├── capability-map.md
├── actor-and-role-model.md
├── business-process-map.md
├── business-rules-catalog.md
├── business-state-machines.md
├── commercial-model.md
├── subscription-and-billing-model.md
├── artist-and-catalog-model.md
├── campaign-and-roi-model.md
├── customer-success-and-support-model.md
├── legal-security-and-compliance-model.md
├── data-ownership-model.md
├── kpi-catalog.md
├── business-golden-path.md
├── domain-boundaries.md
├── future-specification-map.md
└── traceability.md
```

### Source Code

**Sin cambios en esta spec.** No se crean packages `organizations`, `crm`, `billing`, etc.

---

## Phases (documentales)

| Fase | Contenido | Código |
|------|-----------|--------|
| D0 | Borrador completo de artefactos | No |
| D1 | Revisión humana / contradicciones | No |
| D2 | Ajustes de coherencia + cierre documental 015 | No |
| I* | Implementación por specs futuras | Sí (fuera de 015) |

---

## Complexity Tracking

| Ítem | Nota |
|------|------|
| Redefinición producto B2B vs UX streaming actual | Requiere aprobación humana / posible enmienda Constitución |
| Multi-tenancy organizations | Diseño conceptual; DuckDB actual no multi-tenant org |
| PaymentProvider | Solo abstracción; cero proveedores |
| Precios | Estructura sí; montos no definitivos |

---

## Risks

1. Confundir diseño 015 con producto ya vendible.
2. Mezclar `dim_artista` warehouse con artista empresarial.
3. Implementar billing antes de organizations/identity org-scoped.
4. Asignar números de spec prematuramente.

---

## Next after 015 closure

Seguir `future-specification-map.md` (orden recomendado). **No** abrir carpetas hasta autorización explícita.
