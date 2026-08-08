# Constitución Empresarial de Voxmetriks

**Documento:** Constitución del Proyecto Voxmetriks
**Metodología:** GitHub Spec Kit (Spec-Driven Development)
**Alcance:** Repositorio `voxmetriks` — plataforma musical B2B con experiencia personal de escucha
**Autoridad:** Este documento prevalece sobre documentación ad hoc no registrada en Specify.

**Version**: 2.1.0 | **Ratified**: 2026-06-19 | **Last Amended**: 2026-08-08

**Enmienda 2.1.0:** consolidación documental (features activas → `.specify/features/`, historial → `.specify/history/`, verdad de producto → `docs/STATUS.md`). **Sin cambio de principios** (P0–P20 conservados). Inventarios, conteos de endpoints y detalles obsoletos se retiraron; los principios no.

**Vocabulario de estado:**

| Etiqueta | Significado |
|----------|-------------|
| **Implementado** | Existe en código con evidencia de uso o prueba |
| **Parcial** | Existe incompleto, con deuda conocida |
| **Diseñado** | Aprobado en modelo; aún no implementado |
| **Diferido** | Aplazado explícitamente |
| **Fuera de alcance** | Excluido |
| **No comprobado** | Afirmado sin evidencia en este repositorio |

---

## 1. Propósito

VOXMETRIKS es una **plataforma B2B SaaS de gestión e inteligencia musical** (organizaciones, catálogo, comercial, analítica) que incluye una **experiencia personal de escucha** (biblioteca, reproducción, descubrimiento) como capacidad de exploración y demostración académica — **no** como streaming comercial licenciado.

Cadena de diseño: negocio → OE → OT → capacidades → procesos → actores → CU → reglas → estados → datos → backend → frontend → reportes → KPIs → pruebas → evidencia.

---

## 2. Principios arquitectónicos (P0–P20)

Todo cambio MUST evaluarse contra estos principios. Un PR que viole un principio MUST incluir justificación explícita y plan de remediación en la spec asociada.

### P0. Cadena de diseño (negocio → evidencia)

El razonamiento y la documentación de cambios relevantes MUST seguir la cadena negocio → objetivos → capacidades → procesos → actores → casos de uso → reglas → estados → datos → backend → frontend → reportes → KPIs → pruebas → evidencia. MUST NOT inventar dominios empresariales vacíos ni afirmar diseño como implementado.

### P1. Evolución sobre reescritura

El sistema existente es un activo funcional. Las mejoras MUST ser incrementales sobre la base actual. Refactors MUST preservar contratos API públicos salvo spec de breaking change. Migraciones de esquema MUST ser idempotentes.

### P2. Package-by-domain

La organización del código MUST seguir dominios técnicos alineados entre capas (`apps/backend/app/packages/*`, frontend por dominio). Los dominios empresariales solo se materializan en código tras spec de implementación aprobada. MUST NOT crear directorios de dominio sin código real ni spec activa.

### P3. Medallion Data Architecture

Toda ingesta MUST fluir Bronze → Silver → Gold antes del consumo analítico. No se permite carga directa a tablas dimensionales sin staging documentado. Cada ejecución MUST registrar estado en `ctl_*`.

### P4. Autoridad única de warehouse + límites SaaS

La fuente analítica canónica es el DuckDB resuelto por configuración (`data/warehouse/voxmetrik.duckdb`). DuckDB es válido para contexto académico, warehouse analítico y demo local. MUST NOT presentarse como arquitectura transaccional definitiva de un SaaS multiusuario, ni como prueba de alta concurrencia/HA/escala internacional. Operaciones empresariales futuras MUST diseñarse para migración del almacenamiento transaccional cuando la spec lo autorice.

### P5. Schema introspection over assumption

El backend MUST NOT asumir columnas de tablas DuckDB. Los servicios MUST usar introspección segura (`get_table_columns()`, `table_exists()`, `safe_query()` o equivalentes vigentes).

### P6. Separación warehouse / application data

- **Warehouse** (`dim_*`, `fact_*`, `agg_*`, `raw_*`, `ctl_*`): poblado por ELT; lectura principal para analytics.
- **Application** (`app_*`): poblado por API en startup/mutaciones; sesión, playlists, favoritos y estado de aplicación.

### P7. ELT-before-API

La API MUST validar existencia del warehouse en startup. Endpoints analíticos MUST degradar gracefully si faltan agregados; `/health` MUST reportar estado real.

### P8. Spec-Driven Development (SDD)

Todo cambio estructural o feature no trivial MUST seguir Spec Kit: Constitution → Specify → [Clarify] → [Checklist] → Plan → Tasks → [Analyze] → Implement.
**Features activas:** `.specify/features/<NNN-name>/`.
**Historial cerrado:** `.specify/history/` — jamás para features nuevas.
MUST NOT recrear un almacén de features en la raíz del repositorio ni bajo `automation/` como sustituto de `.specify/features/`.

### P9. Contract-first API

La OpenAPI en `/docs` es la referencia de contrato. Modelos Pydantic y DTOs del frontend MUST mantenerse alineados.

### P10. Límite explícito de datos sintéticos

Datos sintéticos MUST identificarse como **synthetic** en specs, respuestas API (metadata cuando aplique) y documentación. MUST NOT presentarse como telemetría de producción.

### P11. Security-by-default en mutaciones

Endpoints que mutan catálogo warehouse, generan datos sintéticos masivos o exponen explorer MUST requerir autenticación y autorización. Deuda conocida MUST remediarse vía spec, no ampliarse.

### P12. Observabilidad como capacidad de primera clase

Logging estructurado, correlación de requests y métricas de pipeline MUST tratarse como requisitos de diseño, no como afterthought.

### P13. Aislamiento multi-organización

Los datos empresariales MUST aislarse por organización cuando el dominio lo requiera. Funciones empresariales MUST exigir contexto de organización. Acceso cross-org de plataforma MUST ser temporal, justificado y auditado.

### P14. Ownership único por dominio

Cada entidad conceptual MUST tener un único dominio propietario. Las dependencias entre dominios MUST ser acíclicas (p. ej. subscriptions no lee tablas internas de billing).

### P15. Mínimo privilegio, separación de funciones y auditoría

Roles de organización y de plataforma MUST distinguirse. Operaciones sensibles MUST aplicar mínimo privilegio, separación de funciones y auditoría.

### P16. Procesos end-to-end con estados explícitos

Capacidades empresariales MUST modelarse como procesos con estados, transiciones, excepciones, aprobaciones y operaciones prohibidas antes de implementar.

### P17. Dinero trazable

Flujos financieros MUST contemplar factura, intento de pago, pago, asignación, conciliación, reembolso, nota de crédito, ledger no destructivo, idempotencia y moneda coherente. MUST NOT almacenar PAN/CVV. MUST NOT afirmar pasarela real implementada sin evidencia.

### P18. KPIs con fórmula/fuente y ROI comprobable

Todo KPI oficial MUST declarar fórmula, fuente, granularidad, frecuencia, propietario, limitaciones y tratamiento de nulos/denominador cero. ROI MUST calcularse solo con ingreso atribuible aprobado; si no, reportar **No disponible**. Streams/engagement MUST NOT convertirse en dinero sin fuente aprobada.

### P19. Naming honesto

MUST NOT usar “AI”, “Enterprise” o “RC” para sugerir capacidades inexistentes. Capacidades AI MUST describirse según evidencia (asistidas/reglas locales, no LLM mágico inventado).

### P20. Honestidad de madurez

Docs y specs MUST etiquetar capacidades como implementado, parcial, diseñado, diferido, fuera de alcance o no comprobado. Diseño ≠ implementado.

---

## 3. Restricciones tecnológicas esenciales

| Capa | Tecnología oficial |
|------|--------------------|
| API | FastAPI (`apps/backend`) |
| SPA | Angular (`apps/frontend`) |
| Warehouse / ELT | DuckDB + `analytics/elt` |
| Runtime local | `compose.yml` + `infrastructure/docker/Dockerfile` + `apps/frontend/Dockerfile` |

Monorepo: `apps/`, `analytics/`, `automation/`, `.specify/`, `docs/`.
Stack inmutable salvo enmienda constitucional. MUST NOT reescribir backend/frontend “desde cero” ni sustituir FastAPI/Angular sin ratificación.

---

## 4. Seguridad y datos

- Autenticación por sesión; códigos de email con límites de intentos.
- RBAC org-scoped (`X-Organization-Id`), aislamiento de tenant, permisos de módulo.
- Artist Space / invitaciones con token seguro; platform ops sin bypass indebido.
- Integridad de billing (idempotencia de refunds), reset de password atómico, sin PII filtrada en perfiles household.
- DuckDB: warehouse analítico / demo — **no** OLTP de producción.
- Pagos: mock / transferencia manual académica; **sin** pasarela real afirmada.
- Audio: contrato YouTube Data API / proveedores aprobados + demos; **sin** licencia comercial de streaming.
- Royalties/payouts reales: **diferidos / fuera de alcance** comercial.

---

## 5. Flujo SDD y gates mínimos

1. Spec Kit (`.specify/features/`) para features activas.
2. Specs históricas en `.specify/history/` (no son verdad de runtime).
3. Estado de producto en `docs/STATUS.md`.
4. Implementación → pruebas → evidencia → cierre.

Gates mínimos: `create_app()`; `python -m pytest` (cwd `apps/backend`); frontend `npm run lint` / `npm test` / `npm run build`; `git diff --check`; Compose canónico cuando Docker esté disponible.

---

## 6. Governance (versionado semántico)

- **MAJOR:** cambio de principios (P0–P20), stack inmutable o redefinición de producto.
- **MINOR:** nuevos principios o restricciones esenciales sin romper los existentes.
- **PATCH:** clarificaciones, compactación documental, corrección de rutas/herramientas sin alterar principios.

Esta enmienda **2.1.0** es MINOR documental: compacta el texto, preserva P0–P20 y alinea rutas Spec Kit (`.specify/features` / `.specify/history`).

---

## 7. Glosario breve

| Término | Definición |
|---------|------------|
| Organización | Tenant B2B pagador / contexto |
| Espacio | Contexto de UI (personal / org / artist / platform) |
| Spec Kit feature | Unidad bajo `.specify/features/` |
| Spec histórica | Documento bajo `.specify/history/` |
| Warehouse | DuckDB analítico Medallion |
