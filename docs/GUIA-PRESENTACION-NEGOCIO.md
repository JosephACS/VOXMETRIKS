# Guía de presentación del negocio — VOXMETRIKS

**Duración objetivo:** ≤ 7 minutos
**Cuenta principal:** `demo.business`
**Contraseña:** variable `DEMO_ACCOUNT_PASSWORD` (no verbalizar ni proyectar el valor)
**Organización:** VOXMETRIKS Demo

Si una pantalla falla, usa el **plan B** de cada paso y sigue. No improvises cifras: usa solo las de la guía maestra.

---

## Preparación (30 s antes)

1. Backend y frontend arriba.
2. Seed ejecutado: `VOXMETRIKS_SEED_DEMO_ACCOUNTS=1` + `DEMO_ACCOUNT_PASSWORD`.
3. Login con `demo.business`.
4. Confirmar menú reducido: PERSONAL / VENTAS / ORGANIZACIÓN / COBROS / RESULTADOS.
5. Tener a mano: **89 740 canciones**, **900 000 eventos sintéticos**, pagos **mock**.

---

## Minuto 0:00–0:40 — Apertura

| Campo | Contenido |
|-------|-----------|
| **Cuenta** | `demo.business` |
| **Pantalla** | Login → Inicio |
| **Ruta** | `/login` → `/discover` |
| **Acción** | Iniciar sesión y mostrar el menú lateral |
| **Debe aparecer** | Menú reducido de 5 grupos; org VOXMETRIKS Demo seleccionable |
| **Texto exacto** | «VOXMETRIKS es una plataforma de música y de negocio musical. Hoy demostraré cómo genera ingresos: primero con personas (B2C) y después con empresas (B2B). Uso una cuenta de presentación con menú reducido; el sistema completo sigue disponible para otras cuentas.» |
| **Pregunta probable** | ¿Por qué el menú es tan corto? |
| **Respuesta** | «Es solo la UI de presentación: filtramos el menú para enfocarnos en ingresos. Las rutas y módulos no se borraron.» |
| **Plan B** | Si el menú sale completo: verificar `username=demo.business` o `preferences.presentation_nav`. Relogin. |

---

## Minuto 0:40–2:10 — B2C: Free → planes → Premium → factura → pago

| Campo | Contenido |
|-------|-----------|
| **Cuenta** | `demo.business` (ya Premium Individual) *o* contraste verbal con `listener.free` si está abierta en otra ventana |
| **Pantalla** | Planes personales → Plan personal → Facturación personal |
| **Rutas** | `/account/plans` → `/account/subscription` → `/account/billing` |
| **Acción** | Mostrar catálogo Free/Premium/Duo/Familiar; abrir plan activo; abrir factura e intento de pago mock |
| **Debe aparecer** | Planes personales listados; suscripción Premium Individual; factura(s) personal(es); pago marcado como mock/simulado |
| **Texto exacto** | «En B2C vendemos a personas. Free es la puerta de entrada. Premium Individual, Duo y Familiar son planes de pago. El usuario genera una factura personal y el cobro en este laboratorio es simulado: no hay pasarela bancaria real. Así demostramos el ciclo Free → plan → factura → pago sin dinero real.» |
| **Pregunta** | ¿Duo y Familiar son lo mismo que una organización? |
| **Respuesta** | «No. Duo/Familiar son *household*: grupo de oyentes. Una *organización* es una empresa B2B.» |
| **Plan B** | Si no hay factura: ir a Planes, repetir checkout mock, o explicar con `listener.premium` sin inventar montos. |

---

## Minuto 2:10–3:10 — Puente CRM (disquera / venta)

| Campo | Contenido |
|-------|-----------|
| **Pantalla** | Panel CRM → Prospectos → Oportunidades |
| **Rutas** | `/crm/dashboard` → `/crm/prospects` → `/crm/opportunities` |
| **Acción** | Mostrar embudo: lead → oportunidad |
| **Debe aparecer** | Cards/tablas con registros demo etiquetados sintéticos/demo |
| **Texto exacto** | «Para B2B no empezamos por la factura: empezamos por ventas. Un prospecto es un cliente potencial; la oportunidad es el negocio en negociación. Aquí la disquera o el equipo comercial empuja el trato hasta un plan empresarial.» |
| **Pregunta** | ¿Esos prospectos son clientes reales? |
| **Respuesta** | «Son datos demo/sintéticos del seed académico, etiquetados para no confundirlos con producción.» |
| **Plan B** | Si CRM vacío: mencionar que el seed crea prospectos; mostrar tabla vacía y pasar a suscripciones org. |

---

## Minuto 3:10–4:40 — B2B: org → plan empresarial → suscripción → factura → pago

| Campo | Contenido |
|-------|-----------|
| **Pantallas** | Estado org → Plan de la organización → Planes empresariales → Facturas → Intentos de pago → Conciliación |
| **Rutas** | `/organizations/{id}/settings` → `/subscriptions/overview` → `/subscriptions/plans` → `/billing/invoices` → `/billing/payment-attempts` → `/billing/reconciliation` |
| **Acción** | Mostrar org activa **VOXMETRIKS Demo**, plan Professional (demo), catálogo Starter/Professional/Business/Enterprise, factura pagada/pendiente e intento mock, conciliación |
| **Debe aparecer** | Org demo; overview de suscripción; lista de planes B2B; facturas; intentos; pantalla de conciliación |
| **Texto exacto** | «En B2B el cliente es una organización. Tiene miembros, un plan empresarial y facturas propias. Starter, Professional, Business y Enterprise cambian capacidad y precio según el catálogo del producto. El pago sigue siendo mock. La conciliación cruza facturas con pagos para demostrar control financiero.» |
| **Pregunta** | ¿Qué es un seat o un entitlement? |
| **Respuesta** | «Seat = cupo de usuario del plan. Entitlement = derecho concreto que el plan desbloquea.» |
| **Plan B** | Si billing falla por permiso: confirmar rol `billing_manager` y org activa; no usar `platform.admin` en esta demo. |

---

## Minuto 4:40–5:40 — Resultados

| Campo | Contenido |
|-------|-----------|
| **Pantalla** | Panel empresarial |
| **Ruta** | `/business-analytics` |
| **Acción** | Señalar ingresos / métricas B2C-B2B disponibles en el panel |
| **Debe aparecer** | Dashboard empresarial con KPIs (según datos seed + warehouse) |
| **Texto exacto** | «Cierro con resultados: aquí la organización ve el efecto del cobro y la operación. VOXMETRIKS no es solo un reproductor: es un modelo de ingresos dual.» |
| **Pregunta** | ¿MRR y ARR están calculados en vivo? |
| **Respuesta** | «El sistema modela suscripciones y facturación; donde el KPI esté materializado en pantallas/seed se muestra. No invento un número si no aparece en pantalla.» |
| **Plan B** | Si el panel carga vacío: volver a Facturas y decir “la evidencia de ingreso está en cobros”. |

---

## Minuto 5:40–6:20 — Regalías (si hay tiempo)

| Campo | Contenido |
|-------|-----------|
| **Pantalla** | Dashboard regalías / fondos |
| **Ruta** | `/royalties` |
| **Acción** | Mostrar fondo distribuible ≠ ingreso de plataforma; badge “Pago simulado” |
| **Texto exacto** | «Después del cobro, finanzas puede aprobar un fondo para regalías. No hay un 70 % universal: el split sale del contrato de derechos (por ejemplo 60/40). El payout es simulado.» |
| **Pregunta** | ¿Ya les pagan a los artistas? |
| **Respuesta** | «Calculamos y simulamos el desembolso. No hay pasarela bancaria real.» |
| **Plan B** | Saltar y mantener discurso de diseño Spec 030. |

## Minuto 6:20–7:00 — Catálogo e inventario de datos

| Campo | Contenido |
|-------|-----------|
| **Pantalla** | Inicio (KPIs) o mención verbal si el explorador no está en el menú |
| **Ruta** | `/discover` |
| **Acción** | Mostrar conteos de canciones/artistas/eventos en home si visibles |
| **Debe aparecer** | Referencias a catálogo warehouse; tip de eventos sintéticos |
| **Texto exacto** | «El catálogo musical es importado: hay 89 740 canciones, 31 429 artistas y 46 154 álbumes. Encima generamos 900 000 eventos analíticos sintéticos derivados de ese catálogo para alimentar analítica sin fingir que sea tráfico de producción.» |
| **Pregunta** | ¿Entonces las reproducciones son falsas? |
| **Respuesta** | «Son sintéticas con propósito académico, derivadas del catálogo importado, y están clasificadas como synthetic en el inventario.» |
| **Plan B** | Si los KPIs no cargan: citar el inventario documentado de la guía maestra. |

---

## Minuto 6:40–7:00 — Cierre

| Campo | Contenido |
|-------|-----------|
| **Acción** | Logout opcional |
| **Ruta** | menú usuario → Cerrar sesión |
| **Texto exacto** | «En siete minutos: B2C cobra a personas, B2B cobra a organizaciones, el CRM alimenta la venta, la facturación cierra el dinero, y el warehouse sostiene la evidencia. Gracias.» |
| **Pregunta** | ¿Puedo ver ELT? |
| **Respuesta** | «Sí, con una cuenta engineer/admin; esta cuenta de presentación lo oculta a propósito.» |
| **Plan B** | Si preguntan módulos ocultos: abrir otra cuenta (`organization.owner` / `platform.admin`) *sin* cambiar `demo.business`. |

---

## Checklist post-demo

- [ ] Login `demo.business`
- [ ] Menú reducido
- [ ] Planes personales
- [ ] Planes empresariales
- [ ] Facturas + intentos + conciliación
- [ ] Panel empresarial
- [ ] Mención 89 740 / 900 000
- [ ] Logout

## Cosas que no debes afirmar

- Que los pagos son con tarjeta real de producción.
- Que los derechos de catálogo son licencias legales firmadas.
- Cifras de dinero que no salgan en pantalla.
- Que `demo.business` es administrador global.
