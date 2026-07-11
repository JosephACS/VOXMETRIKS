# Traceability — Spec 015

**Status**: **CLOSED_WITH_DEFERRED_DECISIONS** (2026-07-11)  
**Evidencia:** `evidence/spec-closure.md`

Cadena: negocio → OE → OT → capacidades → procesos → actores → CU → reglas → estados → datos → backend → frontend → reportes → KPIs → pruebas → evidencia.

---

## 1. Cadena maestra (pagador)

| Nivel | Artefacto |
|-------|-----------|
| Negocio | B2B SaaS (`business-model.md`) — decisión #1–2 aprobadas |
| OE | OE-02 (`strategic-model.md`) |
| Procesos | P-A / P-A-alt, P-C, P-D, P-E |
| Actores | sales_* (plataforma); billing_manager / finance (org) |
| Estados | org ≠ subscription ≠ access |
| Datos | 54 entidades / dueño único |
| Eventos | catálogo canónico (`business-state-machines.md`) |
| KPIs | 49 filas KPI-* |
| Backend/FE | **Futuro** (Identity & Organizations primero) |
| Evidencia | `evidence/*` |

---

## 2. Decisiones

- Aprobadas: `evidence/approved-decisions.md`  
- Diferidas: `evidence/deferred-decisions.md`  

---

## 3. Contradicciones residuales con el sistema actual (no bloquean cierre)

Documentadas, no “arregladas” con código:

1. Constitución aún enfatiza UX streaming — **enmienda diferida**.  
2. “Enterprise” en código = analytics ≠ CRM/billing.  
3. Roles técnicos ≠ RBAC org + sales internos.  
4. `dim_artista` ≠ artist_profile/rights.  
5. Sin organizations; usuario-sin-org **conservado temporalmente** (decisión #7).  
6. DuckDB académico ≠ SaaS transaccional definitivo (decisión #9).  
7. Audio: términos de proveedor **no verificados**.  
8. Auth = sesiones bearer (no JWT afirmado).  

---

## 4. Qué no se tocó (por autorización)

- `.specify/feature.json`  
- `.specify/memory/constitution.md`  
- `automation/specs/TRACEABILITY-MASTER.md`  
- Código / DuckDB / APIs / specs posteriores  

---

## 5. Siguiente paso (humano)

Abrir **Identity & Organizations** cuando se autorice — **sin número definitivo en este cierre**.
