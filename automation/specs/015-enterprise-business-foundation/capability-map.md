# Capability Map — Spec 015

**Status**: Diseñado (con clasificación honesta vs sistema actual)  
**Fecha**: 2026-07-11

| ID | Capacidad | Estado | Evidencia / nota |
|----|-----------|--------|------------------|
| CAP-01 | Autenticación de usuario | **Implementado** | `identity` / auth actual |
| CAP-02 | Autorización técnica (user/engineer/admin) | **Parcial** | No equivale a roles B2B org |
| CAP-03 | Organizations multi-tenant | **Diseñado** | No en código |
| CAP-04 | Membresías e invitaciones | **Diseñado** | |
| CAP-05 | CRM (prospect→contrato) | **Diseñado** | |
| CAP-06 | Planes y precios configurables | **Diseñado** | |
| CAP-07 | Suscripciones y cambios | **Diseñado** | |
| CAP-08 | Facturación e impuestos configurables | **Diseñado** | |
| CAP-09 | Pagos vía PaymentProvider | **Diseñado** | Sin proveedor |
| CAP-10 | Conciliación y mora | **Diseñado** | |
| CAP-11 | Perfiles de artista empresariales | **Diseñado** | ≠ solo `dim_artista` |
| CAP-12 | Derechos y contratos de catálogo | **Diseñado** | |
| CAP-13 | Campañas, presupuestos, aprobaciones | **Diseñado** | |
| CAP-14 | ROI y atribución | **Diseñado** | analytics engagement **parcial** como insumo |
| CAP-15 | Engagement / listening analytics | **Parcial** | warehouse + packages analytics |
| CAP-16 | Reportes ejecutivos y decisiones | **Diseñado** | dashboards actuales ≠ business_decision |
| CAP-17 | Customer success / health | **Diseñado** | |
| CAP-18 | Soporte (tickets) | **Diseñado** | |
| CAP-19 | Compliance / consentimiento / audit | **Diseñado** | audit técnico parcial posible |
| CAP-20 | Exploración audio (YT/Audius/demo) | **Parcial** | no comercial |
| CAP-21 | Streaming comercial licenciado | **Fuera de alcance** | |
| CAP-22 | ELT / calidad warehouse | **Parcial** | analytics/elt canónico (014) |
| CAP-23 | Platform ops / health | **Parcial** | |

## Dependencias de capacidad (orden lógico)

```text
CAP-01 → CAP-03 → CAP-04 → CAP-05 → CAP-06 → CAP-07 → CAP-08 → CAP-09 → CAP-10
                ↘ CAP-11 → CAP-12 → CAP-13 → CAP-14
CAP-15 → CAP-16
CAP-07 → CAP-17 → CAP-18
CAP-03 → CAP-19
```
