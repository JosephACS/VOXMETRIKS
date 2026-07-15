# Mapa integral de negocio — VOXMETRIKS

**Audiencia:** defensa académica · lenguaje sencillo primero, técnico después.

## Ciclo único (historia del producto)

1. Artista/disquera **sube** música (privada).
2. Revisión de metadatos + **derechos**.
3. **Publicación** → búsqueda y reproducción.
4. Oyentes generan **eventos**.
5. Personas y empresas **pagan suscripciones** (mock).
6. Finanzas aprueba un **fondo distribuible**.
7. Atribución → contrato → **regalías** → statement → **payout simulado**.
8. KPI, reportes y decisiones (sin mezclar conceptos).

---

## Por actor

### Oyente personal (B2C)

**Sencillo:** entra, escucha, puede pagar Premium/Duo/Familiar, ve su factura.
**Técnico:** Spec 001/029 · `/discover` · `/account/*` · `personal_*` tables · mock pay · entitlements Free/Individual/Duo/Familiar.
**No ve:** CRM, finanzas org, derechos globales.

### Household

**Sencillo:** un plan familiar compartido entre personas.
**Técnico:** `/account/household` · **no** es organización B2B.

### Artista (`demo.artist`)

**Sencillo:** sube canciones, espera revisión, publica, consulta regalías simuladas.
**Técnico:** Spec 031 · `/artist/*` · `catalog_publishing` · media privada/pública · Spec 021 contracts · Spec 030 statements lectura.
**No ve:** otros artistas, CRM, pools globales.

### Disquera / organización

**Sencillo:** vende y opera como empresa: CRM → plan → factura → analítica.
**Técnico:** Spec 016–019 · `/organizations` `/crm` `/subscriptions` `/billing` · seats/entitlements.

### Ventas (`sales.manager`)

CRM prospectos/oportunidades. Sin payouts ni derechos.

### Finanzas (`finance.manager`)

Facturas, conciliación, fondos/settlements/payouts **simulados**. Sin editar % contractuales.

### Derechos / revisor

Contratos, % = 100, territorios, conflicto; revisión de catálogo Spec 031.

### CS / Soporte / Compliance / Ops / Platform admin

Specs 025–027 · flujos académicos · **sin** certificación GDPR/ISO afirmada.

### Presentación (`demo.business`)

Menú reducido ingresos B2C/B2B + regalías **lectura**.

---

## Qué es cada tipo de dato

| Etiqueta | Significado |
|----------|------------|
| IMPORTADO | Catálogo warehouse (~89 740 tracks) |
| SINTÉTICO | Eventos ACTIVITY (~900 000) derivados |
| DEMO | Seeds etiquetados |
| SIMULADO | Pagos y payouts sin banco real |
