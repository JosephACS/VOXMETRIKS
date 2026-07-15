# Resumen rápido — presentación VOXMETRIKS

*(Máximo ~2 páginas. Imprimible.)*

## 30 segundos

VOXMETRIKS es una plataforma de **música + negocio musical**. A personas les vende planes **B2C** (Free/Premium). A empresas (disqueras) les vende planes **B2B** con CRM, suscripción, factura y cobro. El catálogo es **importado**; ~**900 000** eventos son **sintéticos**; los pagos son **mock**.

Cuenta de presentación: **`demo.business`** (menú reducido). Contraseña: `DEMO_ACCOUNT_PASSWORD` (no escribirla aquí).

## Flujo B2C

Free → Planes personales → Premium → Factura personal → Pago simulado.

Rutas: `/account/plans` · `/account/subscription` · `/account/billing`

## Flujo B2B

Disquera (organización) → Plan empresarial → Suscripción → Factura → Pago mock → Conciliación → Panel resultados.

Rutas: `/subscriptions/*` · `/billing/*` · `/business-analytics` · CRM `/crm/*`

## Diferencias clave

| | B2C | B2B |
|--|-----|-----|
| Cliente | Persona | Organización |
| Agrupación | Household (Duo/Familiar) | Miembros / seats |
| Menú típico | Cuenta personal | CRM + suscripciones + cobros |
| Factura | Personal | Empresarial |

## Vocabulario esencial

- **Subir ≠ publicar** — privado hasta aprobación (Spec 031)
- **B2C / B2B** — vender a persona / a empresa
- **Fondo distribuible / regalía / payout** — Spec 030 (simulado)
- **Contrato de derechos** — % por obra, no 70 % universal
- **Mock / sintético** — laboratorio académico

## Preguntas probables → respuestas

| Pregunta | Respuesta corta |
|----------|-----------------|
| ¿Cómo sube música un artista? | Portal `demo.artist`: borrador → audio/portada privados → envío a revisión → aprobación → publicar. |
| ¿Al subir ya se oye en el catálogo? | No. Solo tras **publicar**. |
| ¿Quién revisa? | `catalog_reviewer` / admin con `publishing.review` + rights gate. |
| ¿Cobran de verdad? | No: pagos mock. |
| ¿70 % al artista? | No universal; sale del contrato (ej. 60/40). |

## Datos técnicos principales (verificados)

| Ítem | Valor |
|------|------:|
| Specs | 31 (001–031; inventario histórico de guía puede desfasarse) |
| Tracks / eventos | 89 740 / 900 000 |

**Spec 031:** subir ≠ publicar · cuenta `demo.artist` · media `data/media`.

Detalle: `docs/GUIA-MAESTRA-VOXMETRIKS.md`.

## No afirmar

- Dinero real cobrado a clientes.
- Licencias legales reales de derechos.
- Números que no salgan en pantalla o inventario.
- Que esta cuenta tenga rol `owner` / `platform_admin`.
