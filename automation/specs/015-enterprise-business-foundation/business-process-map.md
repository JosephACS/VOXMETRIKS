# Business Process Map — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  

Detalle: `operational-model.md`.

---

## Mapa de valor (nivel 0)

```text
Adquirir
  A) Sales-assisted (principal)  |  B) Self-service (alternativo)
  → Contratar / provisionar org
    → Cobrar (factura + pago) o trial
      → Activar entitlements
        → Operar (artistas, derechos, campañas, analytics)
          → Medir → Decidir → Renovar / Expandir
```

---

## Inventario

| ID | Proceso | Área | Dominios | Criticidad |
|----|---------|------|----------|------------|
| P-A | Gestión comercial sales-assisted | Comercial plataforma | crm, contracts | Alta |
| P-A-alt | Adquisición self-service | Producto | identity, organizations, subscriptions, billing | Alta |
| P-B | Organización y membresías | Administración | organizations, identity | Alta |
| P-C | Suscripción / entitlements | Admin/Finanzas prod | subscriptions | Alta |
| P-D | Facturación | Finanzas | billing | Alta |
| P-E | Pagos, conciliación, mora | Finanzas | billing (+ orquestación access) | Alta |
| P-F | Gestión artística | Artística | artists | Media |
| P-G | Catálogo y derechos | Derechos | catalog_rights | Alta |
| P-H | Campañas y ROI | Marketing | campaigns | Alta |
| P-I | Actividad y analítica | Datos | engagement, analytics, reporting | Alta |
| P-J | Customer Success | CS | customer_success | Media |
| P-K | Soporte | Soporte | support | Media |
| P-L | Seguridad y cumplimiento | Seguridad | compliance, platform | Alta |

---

## Hand-offs

1. CRM/contracts → organizations (conversión).  
2. subscriptions events → billing documents.  
3. billing Payment* → orchestration → access/entitlements.  
4. catalog_rights → campaigns gate.  
5. analytics/campaigns → reporting → decisions.  
6. CS → sales (expansión).

---

## Actual vs diseñado

| Proceso | Hoy |
|---------|-----|
| P-I parcial | ELT + dashboards |
| Auth parcial | identity sin org B2B |
| P-A…P-H, P-J…P-L SaaS | **No implementados** |
