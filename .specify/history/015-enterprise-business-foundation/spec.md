> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Enterprise Business Foundation

**Feature Branch**: `015-enterprise-business-foundation` *(propuesta; Git gestionado por el usuario)*  
**Feature Directory**: `.specify/history/015-enterprise-business-foundation/`  
**Created**: 2026-07-11  
**Status**: **CLOSED_WITH_DEFERRED_DECISIONS** (cierre documental 2026-07-11) — ver `evidence/spec-closure.md`  
**Input**: Definir la fundación empresarial B2B SaaS de VOXMETRIKS (negocio → KPIs → evidencia) sin implementar código, DuckDB, APIs ni UI.  
**Revisión externa:** NEEDS_CORRECTIONS corregido y revalidado; decisiones humanas aprobadas/diferidas en `evidence/`.

**Número de spec:** **015** (siguiente disponible tras 014-repository-stabilization-domain-foundation, cerrada `CLOSED_WITH_ACCEPTED_DEBT`).

**Prerrequisitos:** Constitución v1.1.0; specs 001–014; estabilización package-by-domain (014).

---

## Definición oficial del producto

> VOXMETRIKS es una **plataforma B2B SaaS de gestión e inteligencia musical** para artistas, managers, sellos discográficos, agencias y equipos de marketing, finanzas, analítica y dirección.

La **reproducción musical** se conserva como:

| Rol del audio | Estado |
|---------------|--------|
| Función de exploración | **Parcial** (implementado en producto actual) |
| Apoyo a la experiencia | **Parcial** |
| Fuente de eventos de engagement | **Parcial** (warehouse + app events) |
| Capacidad académica de demostración | **Implementado** (demo / proveedores públicos) |
| Servicio comercial de streaming licenciado | **Fuera de alcance** hasta derechos/licencias/integraciones oficiales |

**Negocio principal (diseñado / futuro):** gestionar organizaciones; contratar planes; facturar y cobrar; gestionar artistas y catálogo; administrar campañas y presupuestos; medir rendimiento y ROI; producir reportes; apoyar decisiones; renovar y ampliar clientes.

---

## Principio de diseño obligatorio

```text
negocio → objetivos estratégicos → objetivos tácticos → objetivos operativos
→ capacidades → procesos → actores → casos de uso → reglas de negocio → estados
→ datos → backend → frontend → reportes → KPIs → pruebas → evidencia
```

Prohibido crear módulos, pantallas, tablas o funciones sin conexión demostrable con esta cadena (ver `traceability.md`).

---

## Objetivo de esta spec

Producir un **modelo empresarial coherente y trazable** que sirva de base a specs posteriores de implementación, sin fingir que CRM, billing, organizations u otros dominios ya existen en código.

**Esta spec NO implementa.** Solo diseña.

---

## Vocabulario de estado (obligatorio)

| Etiqueta | Significado |
|----------|-------------|
| **Implementado** | Existe en código con evidencia |
| **Parcial** | Existe incompleto / con adaptadores |
| **Diseñado** | Definido en esta spec; no implementado |
| **Futuro** | Diferido a specs posteriores |
| **Fuera de alcance** | Explicitamente excluido |

---

## User Scenarios & Testing *(documentales)*

### User Story 1 — Modelo de negocio y quién paga (Priority: P1)

Como dirección del producto, necesito un modelo de negocio B2B SaaS claro (problema, pagador, beneficiarios, ingresos, límites) para alinear specs futuras.

**Independent Test**: Leer `business-model.md` + `commercial-model.md` y verificar distinción implementado/diseñado/futuro/fuera de alcance; sin clientes ni ingresos inventados como reales.

**Acceptance Scenarios**:

1. **Given** la definición oficial, **When** se revisa el modelo, **Then** el pagador es la organización B2B y el streaming comercial no es el producto principal.
2. **Given** el estado actual del repo, **When** se clasifica capacidades, **Then** organizations/CRM/billing aparecen como **diseñado/futuro**, no implementado.

---

### User Story 2 — Cadena estratégica → táctica → operativa (Priority: P1)

Como analista de negocio, necesito objetivos medibles conectados a áreas, procesos y KPIs.

**Independent Test**: Cruzar `strategic-model.md` ↔ `tactical-model.md` ↔ `operational-model.md` ↔ `kpi-catalog.md` sin huecos de código de objetivo.

---

### User Story 3 — Flujo de dinero completo (Priority: P1)

Como finanzas / producto, necesito el ciclo organización → plan → factura → pago → renovación (y fallos) con abstracción `PaymentProvider`, sin almacenar PAN/CVV.

**Independent Test**: `subscription-and-billing-model.md` + máquinas de estado de factura/pago + golden path monetario.

---

### User Story 4 — Actores, roles y dominios (Priority: P2)

Como arquitectura, necesito roles org/plataforma, límites de dominio y propiedad de datos conceptuales sin crear carpetas de código.

**Independent Test**: `actor-and-role-model.md` + `domain-boundaries.md` + `data-ownership-model.md`.

---

### User Story 5 — Business Golden Path y mapa de specs futuras (Priority: P2)

Como mantenedor Spec Kit, necesito el recorrido empresarial principal y el orden recomendado de specs posteriores **sin números definitivos** ni carpetas creadas.

**Independent Test**: `business-golden-path.md` + `future-specification-map.md`.

---

### Edge Cases (diseño)

- Pago rechazado → gracia → suspensión → recuperación/cancelación.
- Conflicto de derechos de catálogo → bloqueo de campaña hasta resolución.
- Miembro con roles distintos en dos organizaciones.
- Organización sin perfil fiscal → no emitir factura.
- Health score crítico → intervención CS antes de churn.

---

## Requirements *(documentales)*

### Functional (diseño)

- **FR-001**: Modelo de negocio B2B SaaS documentado con límites explícitos.
- **FR-002**: Objetivos estratégicos con KPI, fórmula, fuente, meta **propuesta**.
- **FR-003**: Áreas tácticas con procesos, roles e información I/O.
- **FR-004**: Procesos operativos A–L con estados, excepciones y auditoría.
- **FR-005**: Modelo de cobro con planes configurables (sin precios definitivos).
- **FR-006**: Máquinas de estado para entidades comerciales y operativas listadas.
- **FR-007**: Roles org + plataforma; transición desde roles técnicos actuales **diseñada**, no reemplazada.
- **FR-008**: Límites de 16 dominios empresariales sin crear código.
- **FR-009**: Modelo de datos conceptual (entidades listadas) sin migraciones DuckDB.
- **FR-010**: Catálogo de KPIs con fórmulas y clasificación actual/futuro/propuesto.
- **FR-011**: Business Golden Path trazable extremo a extremo.
- **FR-012**: Mapa de specs futuras con dependencias (sin números definitivos).

### Non-Functional (diseño)

- **NFR-001**: No presentar futuro como implementado.
- **NFR-002**: No inventar clientes, ingresos, contratos ni cumplimiento legal reales.
- **NFR-003**: No almacenar (ni diseñar almacenamiento de) PAN/CVV completos.
- **NFR-004**: Audio comercial licenciado = fuera de alcance hasta evidencia legal.
- **NFR-005**: Trazabilidad negocio→evidencia obligatoria (`traceability.md`).

---

## Success Criteria (cierre de la 015)

La 015 podrá cerrarse cuando:

1. Exista un modelo empresarial coherente.
2. Estratégico, táctico y operativo estén conectados.
3. Esté definido quién paga y por qué.
4. El flujo de dinero sea completo (éxito y fallo).
5. Actores y permisos estén definidos.
6. Procesos tengan estados y excepciones.
7. Dominios tengan límites.
8. Modelo conceptual tenga propietarios.
9. KPIs tengan fórmulas y fuentes.
10. Business Golden Path sea trazable.
11. Exista mapa de specs futuras.
12. Nada futuro se presente como implementado.

**Cierre de esta entrega:** **CLOSED_WITH_DEFERRED_DECISIONS** — ver `evidence/spec-closure.md`. Spec siguiente no iniciada.

---

## Fuera de alcance (esta spec y ejecución inmediata)

- Implementar código backend/frontend
- Modificar DuckDB / crear tablas
- Cambiar APIs o reorganizar carpetas de packages
- Implementar pagos / proveedores reales
- Modificar reproducción
- Abrir carpetas de specs posteriores
- Modificar `.specify/feature.json` o Constitución (explícitamente diferido)
- Asignar números definitivos a specs futuras

---

## Artefactos de esta carpeta

| Archivo | Contenido |
|---------|-----------|
| `business-model.md` | Problema, clientes, valor, ingresos, límites |
| `strategic-model.md` | Objetivos estratégicos medibles |
| `tactical-model.md` | Áreas empresariales |
| `operational-model.md` | Procesos diarios A–L |
| `capability-map.md` | Capacidades ↔ estado |
| `actor-and-role-model.md` | Roles y permisos |
| `business-process-map.md` | Mapa de procesos |
| `business-rules-catalog.md` | Reglas de negocio |
| `business-state-machines.md` | Estados y transiciones |
| `commercial-model.md` | Comercial / CRM |
| `subscription-and-billing-model.md` | Planes, facturación, pagos |
| `artist-and-catalog-model.md` | Artistas y derechos |
| `campaign-and-roi-model.md` | Campañas y ROI |
| `customer-success-and-support-model.md` | CS y soporte |
| `legal-security-and-compliance-model.md` | Legal / seguridad |
| `data-ownership-model.md` | Entidades conceptuales y dueños |
| `kpi-catalog.md` | KPIs |
| `business-golden-path.md` | Recorrido principal |
| `domain-boundaries.md` | Límites de dominio |
| `future-specification-map.md` | Orden de specs futuras |
| `traceability.md` | Cadena de trazabilidad |
| `plan.md` / `tasks.md` / `checklist.md` | Plan, tareas documentales, gates |

---

## Contradicciones conocidas con el sistema actual

Ver sección dedicada en la entrega final y detalle en `traceability.md` § Contradicciones. Resumen:

1. Constitución/visión aún enfatizan UX streaming + analytics; 015 redefine el **negocio principal** como B2B SaaS de gestión — **diseñado**, requiere enmienda constitucional futura (no en esta entrega).
2. Roles técnicos actuales (`user` / engineer / admin) ≠ roles org B2B — coexistencia diseñada.
3. `dim_artista` / catálogo warehouse ≠ `artist_profile` empresarial con derechos — no confundir.
4. No hay organizations multi-tenant reales; tenancy actual es usuario/sesión.
5. Enterprise API actual = analytics/dashboard, no CRM/billing.

---

## Assumptions

- El pagador es siempre una **organización** (B2B), no el oyente final del demo player.
- Precios y tasas son **configurables**; valores numéricos en docs son **propuestos ilustrativos**, no tarifas reales.
- PaymentProvider admite mock académico, manual, transferencia y pasarela externa en el **futuro**.
- Specs de implementación posteriores consumirán este modelo; 015 no las crea.
