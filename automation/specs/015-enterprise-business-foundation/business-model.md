# Business Model — VOXMETRIKS (Spec 015)

**Status**: Diseñado (borrador)  
**Fecha**: 2026-07-11  
**Nota**: No inventa clientes, ingresos, contratos ni cumplimiento reales.

---

## 1. Problema real

Equipos musicales (artistas, managers, sellos, agencias) operan con herramientas fragmentadas: hojas de cálculo, dashboards de plataformas de streaming de terceros, CRM genérico y finanzas desconectadas. Falta un sistema B2B que una **organización → catálogo/derechos → campañas → analítica → facturación → renovación** con trazabilidad y roles.

El oyente final del demo player **no** es el problema de negocio principal.

---

## 2. Clientes objetivo

| Segmento | Descripción | Estado |
|----------|-------------|--------|
| Sellos / labels independientes | Gestión de roster y campañas | **Diseñado** |
| Managers / management companies | Artistas, equipos, ROI | **Diseñado** |
| Agencias de marketing musical | Campañas, presupuestos, atribución | **Diseñado** |
| Equipos internos de artista (pro) | Catálogo, reportes, colaboración | **Diseñado** |
| Academia / demos institucionales | Exploración y defensa de proyecto | **Parcial** (uso actual del repo) |

**No son clientes pagadores del SaaS (diseño):** oyentes anónimos del player demo.

---

## 3. Cliente pagador

**Organización B2B** (cuenta empresa) que contrata un **plan** y paga facturas.

Persona de facturación típica: `billing_manager` / `finance` / `owner` (ver roles).

---

## 4. Usuarios beneficiarios

| Beneficiario | Valor |
|--------------|-------|
| Owner / admin org | Control, membresías, suscripción |
| Artist manager | Roster, asignaciones |
| Marketing | Campañas, presupuesto, ROI |
| Finance | Facturas, cobranza, mora |
| Analyst | KPIs, reportes |
| Artist (rol limitado) | Visibilidad de su perfil/catálogo autorizado |
| Dirección | Decisiones y reportes ejecutivos |
| Plataforma (support/auditor) | Operación y cumplimiento |

---

## 5. Propuesta de valor

Una sola plataforma para **gestionar la empresa musical** y **medir inteligencia de rendimiento**, con:

- multi-organización y roles;
- suscripción y facturación;
- artistas + derechos de catálogo;
- campañas con aprobación y ROI;
- analítica y reportes accionables;
- customer success y soporte;
- auditoría y cumplimiento básico diseñado.

Audio = exploración / eventos / demo — **no** promesa de Spotify-as-a-service.

---

## 6. Fuentes de ingresos (**diseñadas**)

| Fuente | Notas |
|--------|-------|
| Suscripción mensual | Plan base configurable |
| Suscripción anual | Descuento configurable (no precio fijo aquí) |
| Complementos (add-ons) | Artistas extra, miembros extra, historial, exports, analytics packs |
| Servicios empresariales personalizados | Fuera del self-serve; **futuro** / comercial |

Montos: **configurables** — ver `subscription-and-billing-model.md`. No hay tarifas oficiales en este documento.

---

## 7. Costos principales (**propuestos / conceptuales**)

- Ingeniería y operación de plataforma
- Infraestructura (compute, storage warehouse)
- Soporte y customer success
- Cumplimiento / seguridad
- Pasarela de pagos (fees del proveedor — **futuro**)
- Adquisición comercial (marketing B2B)

No se afirman costos reales del proyecto académico/actual.

---

## 8. Canales

| Canal | Estado |
|-------|--------|
| Producto web (SPA) | **Parcial** (producto actual ≠ B2B completo) |
| Demo académica / defensa | **Parcial** |
| Ventas directas B2B | **Diseñado** |
| Partner / agencias | **Futuro** |
| Self-serve checkout | **Diseñado** |

---

## 9. Relación con clientes

- Onboarding guiado (CS)
- Health score y riesgo de churn
- Soporte por tickets
- Renovación y expansión (upsell add-ons)
- Reportes ejecutivos periódicos (**diseñado**)

---

## 10. Diferenciadores

| Diferenciador | vs genéricos | Estado |
|---------------|--------------|--------|
| Dominio musical (artistas, derechos, campañas) | CRM genérico | **Diseñado** |
| Warehouse + engagement ya existente | BI separado | **Parcial** (analytics actual) |
| Trazabilidad Spec Kit / evidencia | Docs ad hoc | **Parcial** |
| Audio como apoyo, no como promesa legal de streaming | “Spotify clone” | **Diseñado** (límite explícito) |

---

## 11. Riesgos

| Riesgo | Mitigación diseñada |
|--------|---------------------|
| Confusión legal por audio YouTube/Audius | Límites en constitución + legal model |
| Overclaim de “enterprise” sin orgs/billing | Spec 015 + naming honesto |
| DuckDB single-file vs multi-tenant SaaS | Límite de plataforma documentado; evolución **futura** |
| Churn por falta de ROI demostrable | Campañas + KPIs + CS |
| PCI / datos de tarjeta | Solo referencias tokenizadas; PaymentProvider |

---

## 12. Límites del producto

- No es CDN/DRM de audio comercial propio.
- No garantiza derechos Spotify ni distribución global.
- No es banco ni emisor fiscal certificado por sí mismo (integraciones **futuras**).
- Metas KPI = **propuestas**, no resultados medidos de negocio real.
- Multi-región compliance completo = **futuro**.

---

## 13. Qué NO es VOXMETRIKS

- Un Spotify / Apple Music / YouTube Music comercial.
- Un marketplace de beats o tienda DTC de merch (fuera de alcance 015).
- Un ERP contable completo.
- Un CRM genérico sin dominio musical.
- Un producto ya facturando a clientes reales (**no comprobado** / no afirmado).

---

## 14. Matriz de madurez (honesta)

| Capacidad | Estado |
|-----------|--------|
| Catálogo + analytics warehouse | **Parcial** / **Implementado** (técnico) |
| Auth usuario / sesión | **Implementado** (identity técnico) |
| Organizations multi-tenant | **Diseñado** |
| CRM comercial | **Diseñado** |
| Suscripciones / billing / pagos | **Diseñado** |
| Artistas empresariales + derechos | **Diseñado** (≠ solo `dim_artista`) |
| Campañas + ROI | **Diseñado** |
| Customer success / support | **Diseñado** |
| Compliance formal | **Diseñado** |
| Streaming comercial licenciado | **Fuera de alcance** |
