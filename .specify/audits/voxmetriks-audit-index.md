# VOXMETRIKS — Índice de auditoría (paquete de entrega)

| Campo | Valor |
|-------|-------|
| **Documento** | `.specify/audits/voxmetriks-audit-index.md` |
| **Fecha** | 2026-08-06 |
| **Fase** | Auditoría + documentación Spec-Driven — **sin cambios de código funcional** |
| **Feature activa** | 044 — product consolidation and data clarity |
| **Git** | Sin commits / ramas / push en esta fase |

Este índice es el **punto de entrada** para revisión interna y externa. Enlaza todos los artefactos generados y resume el estado de decisión.

---

## 1. Documentos de la auditoría

| # | Documento | Ruta | Contenido |
|---|-----------|------|-----------|
| 1 | Auditoría completa | [voxmetriks-full-audit.md](./voxmetriks-full-audit.md) | Resumen ejecutivo, inventarios FE/BE/datos, clasificación de módulos, problemas, riesgos, rendimiento, seguridad |
| 2 | Auditoría por roles | [voxmetriks-role-audit.md](./voxmetriks-role-audit.md) | Usuario / Admin / Engineer: menús, flujos, permisos, matriz rol–módulo |
| 3 | Plan de simplificación | [voxmetriks-simplification-plan.md](./voxmetriks-simplification-plan.md) | Tabla Elemento → Clasificación → Acción → Riesgo → Orden → Validación |
| 4 | Candidatos a eliminación | [voxmetriks-deletion-candidates.md](./voxmetriks-deletion-candidates.md) | Solo ELIMINAR (con evidencia, dependencias, confianza) |
| 5 | Sistema de diseño (propuesta) | [../design/voxmetriks-design-system-proposal.md](../design/voxmetriks-design-system-proposal.md) | Principios, kit enterprise existente, plantilla CRUD, migración |
| 6 | Checklist capturas visuales | [voxmetriks-visual-review-checklist.md](./voxmetriks-visual-review-checklist.md) | Qué pantallas abrir/capturar por rol; tipos FULL/NAV/FORM/… |
| 7 | Este índice | [voxmetriks-audit-index.md](./voxmetriks-audit-index.md) | Paquete de entrega y guía de segunda revisión |

### Evidencia visual (runtime)

| Ítem | Estado |
|------|--------|
| Carpeta `.specify/audits/evidence/` | **Pendiente** — crear al capturar |
| Capturas automáticas en esta sesión | **No** — sin herramienta de browser capture disponible |
| Acción | Seguir [checklist visual](./voxmetriks-visual-review-checklist.md) de forma **manual** |

### Contexto de producto (ya existente, no generado en esta auditoría)

| Documento | Uso |
|-----------|-----|
| `.specify/memory/constitution.md` | Definición B2B / límites audio |
| `.specify/feature.json` | Feature activa 044 |
| `docs/PRODUCT_FEATURES.md` | MVP visible vs fuera de alcance |
| `apps/frontend/src/app/packages/README.md` | Mapa packages MVP vs demo |
| Specs 033–044 / 038 | Música, nav, hide demos, consolidación |

---

## 2. Resumen ejecutivo (1 párrafo)

VOXMETRIKS tiene un **núcleo demostrable sólido** (música + engagement + Workpanel/reportes + ELT/Explorer) y una **capa enterprise amplia** (CRM, billing, royalties, etc.) implementada pero **ocultada del producto-final** (038). La auditoría recomienda **congelar el claim de demo en el MVP**, limpiar código UI/API muerto con bajo riesgo, fusionar superficies duplicadas (historial/actividad, users/settings, hubs de reportes), y **no borrar** backends/tablas enterprise hasta mapear dependencias de reportes. El diseño CRUD debe **reutilizar** el kit `enterprise-*`, no reinventarlo. La calidad visual **aún no está verificada en runtime**; falta el paquete de capturas.

---

## 3. Clasificación rápida de módulos

| Clasificación | Ejemplos |
|---------------|----------|
| **MANTENER** | Streaming, identity, engagement, organizations, workpanel, reports, data-engineering, settings |
| **MANTENER CON AJUSTES** | Smart/AI (etiquetar), publishing/rights, reporting hub, platform-ops |
| **SIMPLIFICAR** | Nav por rol, hubs de catálogo, paths de reportes |
| **FUSIONAR** | History+Activity; Users→Settings; reports hub; EmptyState/MetricCard |
| **ELIMINAR** (candidatos) | Analytics FE huérfanos, `features/*`, componentes sin uso, shim `packages/users` |
| **POSPONER** | CRM, billing, royalties, campaigns, BA, CS, compliance, subs B2B, personal billing |

Detalle: [full-audit §14](./voxmetriks-full-audit.md) · [deletion-candidates](./voxmetriks-deletion-candidates.md).

---

## 4. Matriz de módulos por rol (resumen)

| Módulo | Usuario | Admin | Engineer |
|--------|:-------:|:-----:|:--------:|
| Discover / Search / Library / Player | ✅ | ○ | ○ |
| Activity (history fusionada) | ✅ | ○ | ○ |
| Settings | ✅ | ✅ | ✅ |
| Organizations | ○ | ✅ | ○ |
| Catalog publishing / rights / artists | ❌ | ✅ | ○ |
| Workpanel | ❌ | ✅ | ✅ |
| Reports hub | ❌ | ✅ | ✅ |
| ELT + Explorer | ❌ | ✅* | ✅ |
| Enterprise demos 038 | ❌ | ❌ | ❌ |

✅ menú producto · ○ acceso opcional/secundario · ❌ fuera producto · \*vía `hasEngineerAccess`  

Detalle completo: [role-audit](./voxmetriks-role-audit.md).

---

## 5. Menús recomendados

| Rol | Menú propuesto |
|-----|----------------|
| Usuario | Discover · Buscar · Canciones · Playlists · Me gusta · Actividad · Configuración |
| Admin | Workpanel · Reportes · Organizaciones · Catálogo · Configuración |
| Engineer | ELT · Explorer · Workpanel · Reportes · Configuración |

---

## 6. Riesgos principales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Borrar tablas/UI enterprise sin mapear SQL de reportes | Alta | Mantener POSPONER; inventariar queries |
| Demo con warehouse vacío | Alta | Checklist pipeline + PB antes de defensa |
| Sobreclaim B2B / IA / compliance / streaming licenciado | Alta | Narrativa MVP 038–044; etiquetas mock/synthetic |
| Webhook billing + audio-source públicos | Alta/Media | Fase seguridad post-aprobación |
| Eliminar `/api/v2` sin deprecación | Media | Confirmar 0 consumidores externos |
| Auth en audio rompe player | Media | E2E playback obligatorio |

Más: [full-audit §8–13](./voxmetriks-full-audit.md).

---

## 7. Orden recomendado de implementación (post-aprobación)

| Orden | Área | Acción | Resultado | Riesgo |
| ----- | ------------------- | ------------------------------ | ------------------------ | ------ |
| 1 | Gobernanza | Aprobar MANTENER / ELIMINAR / POSPONER | Alcance cerrado | Bajo |
| 2 | Arquitectura | Limpiar código muerto (candidatos C1–C7, C11) | Base mantenible | Bajo |
| 3 | Usuario | Nav + fusionar activity/settings | Flujo musical claro | Medio |
| 4 | Administrador | Hub reportes + CRUD kit | Gestión consistente | Medio |
| 5 | Ingeniero | Data Ops + etiquetas datos + bootstrap | Demo técnica clara | Alto |
| 6 | Diseño | Migrar CRUDs al enterprise kit | UI coherente | Medio |
| 7 | Seguridad | Webhook, audio-source, rate limit | Acceso controlado | Alto |
| 8 | Rendimiento | Home / explorer / ELT | Demo estable | Medio |
| 9 | Deprecaciones mayores | `/api/v2`, módulos 038 (solo si se aprueba) | Menos superficie | Alto |
| 10 | Validación | Pruebas integrales + guión demo | Defensa | Medio |

Plan tabular: [simplification-plan](./voxmetriks-simplification-plan.md).

---

## 8. Propuesta de diseño (una línea)

Reutilizar `shared/components/enterprise/*` como CRUD canónico; fusionar EmptyState y MetricCard; listener conserva UI musical; migración pantalla a pantalla tras aprobación.

→ [design proposal](../design/voxmetriks-design-system-proposal.md)

---

## 9. Capturas visuales pendientes

| Sesión | Rol | Capturas clave (IDs) | Doc |
|--------|-----|----------------------|-----|
| 1 | Usuario | U01–U09, U13–U24, U26–U28, U30, U32 | [checklist](./voxmetriks-visual-review-checklist.md) |
| 2 | Admin | A01–A09, A14–A17, A23–A29 | idem |
| 3 | Engineer | E01–E17, E21 + evidencia PB/parquet/DuckDB | idem |

**Estado:** lista lista; **evidencia runtime pendiente del revisor humano**.

---

## Información que debe enviarse para una segunda revisión

Para el debate / revisión externa, compartir este paquete:

1. **Este índice:** `.specify/audits/voxmetriks-audit-index.md`
2. **Documentos principales de la auditoría:**
   - `voxmetriks-full-audit.md`
   - `voxmetriks-role-audit.md`
   - `voxmetriks-simplification-plan.md`
   - `voxmetriks-design-system-proposal.md` (en `.specify/design/`)
3. **Lista de candidatos a eliminación:** `voxmetriks-deletion-candidates.md`
4. **Matriz de módulos por rol:** sección en `voxmetriks-role-audit.md` (y resumen §4 de este índice)
5. **Capturas solicitadas:** según `voxmetriks-visual-review-checklist.md`, guardadas en `.specify/audits/evidence/` cuando existan
6. **Cualquier error** encontrado al abrir las pantallas (consola, network, 403/500, pantallas en blanco) — preferible en `evidence/NOTES.md`
7. **Diferencias** entre lo que indica el código/auditoría y lo **observado en ejecución** (rutas, menús, datos vacíos, mocks no etiquetados, UI rota)

### Formato de entrega sugerido

- Markdown dentro de `.specify` (no Word en esta fase).
- ZIP o enlace al repo + carpeta `evidence/` con PNGs nombrados `NNN-rol-pantalla-estado.png`.
- Lista corta de **decisiones pedidas** al revisor:
  1. ¿Aprobar narrativa MVP 038–044?
  2. ¿Aprobar lista ELIMINAR (C1–C7, C11)?
  3. ¿Mantener enterprise 038 como POSPONER gated?
  4. ¿Priorizar fusiones History/Activity y Users/Settings?
  5. ¿Aceptar enterprise kit como design system CRUD?

---

## 10. Lo que NO se ha hecho (detención obligatoria)

- No se eliminaron módulos ni rutas.
- No se cambió el diseño ni se construyeron componentes nuevos.
- No se refactorizaron CRUD.
- No se cambiaron permisos ni la base de datos.
- No hubo operaciones Git.
- No se generó documento Word.
- No se inventaron capturas ni imágenes representativas.

---

## 11. Siguiente fase

1. Debate y revisión externa con este paquete + capturas.  
2. Aprobación explícita de decisiones.  
3. Solo entonces: implementación **rol por rol** según el orden de §7, con especificación y aprobación por oleada.

**Fin del índice. Auditoría documentada — detenido a la espera de instrucciones.**
