# GUÍA MAESTRA — VOXMETRIKS

**Documento para personas no técnicas y técnicas.**
**Fecha de inventario:** 2026-07-14
**Regla:** todos los números de este documento vienen del repositorio, Specs, inventarios DuckDB verificados o conteos de código. No se inventan cifras.

---

## 1. ¿Qué es VOXMETRIKS? (en palabras sencillas)

**VOXMETRIKS** es una plataforma digital de música y gestión musical con dos caras del mismo negocio:

1. **Para oyentes** (personas): descubrir música, listas, favoritos, historial, y pagar un **plan personal** (Free o Premium).
2. **Para empresas** (disqueras, sellos, equipos comerciales): organizar clientes, vender **planes empresariales**, facturar, cobrar, ver resultados y administrar catálogo/derechos.

Piensa en Spotify/Apple Music por el lado “escuchar”, y en un CRM + facturación + analítica por el lado “empresa”.

### Qué problema resuelve

- A las **personas**: centralizar descubrimiento musical, preferencias y suscripción en un solo producto.
- A las **empresas**: seguir el ciclo comercial completo: prospecto → oportunidad → contrato/plan → factura → pago → métricas.
- Al **proyecto académico**: demostrar con datos reales/importados y datos sintéticos controlados cómo funciona un producto de negocio punta a punta.

### Quiénes son sus usuarios

| Tipo | Ejemplo | Qué hace |
|------|---------|----------|
| Oyente Free / Premium | `listener.free`, `listener.premium` | Escucha, explora, gestiona plan y factura personal |
| Titular de household | `household.owner` | Comparte un plan familiar entre miembros |
| Vendedor / CRM | `sales.manager` | Prospectos y oportunidades |
| Dueño de organización | `organization.owner` | Administra la disquera / empresa |
| Finanzas | `finance.manager` | Facturas, cobros, conciliación |
| Presentación negocio | `demo.business` | Menú reducido centrado en ingresos |
| Ops / admin plataforma | `platform.admin` | Operaciones y catálogos globales |

# Cómo genera dinero

- **B2C:** Free $0 · Individual $4.99/$49.90 · Duo $7.99/$79.90 · Familiar $9.99/$99.90 (mock).
- **B2B:** Starter $49/$490 · Professional $99/$990 · Business $199/$1 990 · Enterprise $499/$4 990 (mock).
- **Regalías 030:** fondo aprobado ≠ ingreso total; payout **simulado**.
- **Publicación 031:** subir ≠ publicar.

Inventario y cierre: `docs/INVENTARIO-FINAL-VERIFICADO.md` · `docs/AUDITORIA-CIERRE-FINAL.md` · estado **ENTERPRISE_ACADEMIC_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT**.

Los pagos en este entorno son **MOCK / simulados** (académicos). No se cobró dinero real a tarjetas bancarias de producción.

### B2C vs B2B (qué significan)

- **B2C (Business to Consumer):** la empresa vende a una **persona**. Aquí: plan Free/Premium, factura personal, hogar (household).
- **B2B (Business to Business):** la empresa vende a **otra empresa**. Aquí: organización (disquera), seats, CRM, facturación empresarial.

### Usuario personal, household y organización

- **Usuario personal:** una cuenta individual (tú y tu plan).
- **Household (hogar/grupo):** un plan Familiar/Duo que agrupa varias cuentas personales bajo un titular.
- **Organización:** la “empresa” dentro del sistema (ej. *VOXMETRIKS Demo*). Tiene miembros, roles, plan empresarial y facturas propias. No es lo mismo que un household.

### ¿Qué datos son reales, importados, sintéticos, demo o simulados?

| Tipo | Significado | En VOXMETRIKS |
|------|-------------|----------------|
| **Importado** | Sacado de datasets externos (catálogo musical) | Canciones, artistas, álbumes en dimensiones `dim_*` |
| **Sintético** | Generado por algoritmos a partir del catálogo | ~900.000 eventos de actividad derivados |
| **Demo** | Sembrado solo para demos académicas | Org *VOXMETRIKS Demo*, prospectos `[SYNTHETIC]`, cuentas `*.demo.voxmetriks.local` |
| **Simulado / MOCK** | Parece un pago/proveedor real, pero no lo es | Checkout mock, intentos de pago mock |
| **Real de producto** | Lógica de negocio real del sistema | RBAC, estados de suscripción, facturas, conciliación de laboratorio |

---

## 2. Glosario completo (técnico y no técnico)

Cada término: **qué es** → **para qué sirve**.

### Negocio

| Término | Qué es | Para qué sirve |
|---------|--------|----------------|
| **B2C** | Venta a consumidor final | Explicar planes personales y facturas de oyente |
| **B2B** | Venta a otra empresa | Explicar planes de organización y CRM |
| **Plan** | Paquete de beneficios con precio | Elegir Free/Premium o Starter/Enterprise |
| **Suscripción** | Contrato activo a un plan | Mantener el acceso mientras se pague |
| **Factura** | Documento de cobro | Mostrar cuánto se debe / se pagó |
| **Pago (mock)** | Intento de pagar en laboratorio | Demostrar flujo de cobro sin banco real |
| **Conciliación** | Cruzar facturas vs pagos | Verificar que lo cobrado cuadre |
| **Refund** | Devolución de dinero | Corregir cobros (en laboratorio) |
| **Credit note** | Nota de crédito | Ajuste contable sin reembolso en efectivo |
| **MRR** | Monthly Recurring Revenue — ingreso mensual recurrente | Medir salud de ingresos |
| **ARR** | Annual Recurring Revenue — MRR×12 (o anualizado) | Hablar de escala anual |
| **past_due** | Suscripción atrasada de pago | Señal de riesgo de churn |
| **Trial** | Periodo de prueba | Probar el plan antes de pagar |
| **Seat** | “Asiento” / licencia de usuario en un plan B2B | Limitar cuántas personas caben en el plan |
| **Entitlement** | Derecho concreto ganado por el plan | Abrir/cerrar capacidades (ej. calidad, módulos) |
| **Project** | Unidad de trabajo/proyecto en contexto empresarial | Agrupar trabajo dentro de la org (cuando aplique el módulo) |
| **SSO** | Single Sign-On — un login para varios sistemas | Capacidad empresarial (puede ser académica/declarada) |
| **SLA** | Service Level Agreement — acuerdo de nivel de servicio | Promesas de disponibilidad/soporte en Enterprise |
| **CRM** | Customer Relationship Management | Gestionar prospectos y oportunidades de venta |
| **Prospecto** | Cliente potencial | Inicio del embudo comercial |
| **Oportunidad** | Negocio en negociación | Mover deal hacia cierre |
| **KPI** | Key Performance Indicator | Número clave de éxito |
| **Customer Success (CS)** | Equipo que ayuda a que el cliente tenga éxito | Retención y expansión |
| **Churn** | Cancelación / pérdida de clientes | Medir fugas de ingreso |
| **ELT** | Extract-Load-Transform (pipeline de datos) | Llevar datos crudos al warehouse |
| **RBAC** | Control de acceso por roles | Decidir quién ve/hace qué |
| **Household** | Grupo familiar | Compartir plan Duo/Familiar |
| **Organización** | Empresa en el sistema | Contenedor B2B |
| **Disquera / sello** | Tipo de organización musical | Ejemplo de cliente B2B |

### Técnica

| Término | Qué es | Para qué sirve |
|---------|--------|----------------|
| **Frontend** | App web que ves (Angular) | Pantallas y navegación |
| **Backend** | API (FastAPI) | Reglas de negocio y datos |
| **Endpoint** | URL de la API (GET/POST…) | Que el frontend pida/guarde datos |
| **Caso de uso** | Acción de negocio encapsulada | “crear factura”, “iniciar trial”… |
| **Package-by-domain** | Código agrupado por dominio (billing, crm…) | Mantener el sistema ordenado |
| **DuckDB** | Base analítica embebida | Warehouse local de demos |
| **Warehouse** | Almacén analítico | dims/facts/aggs |
| **app_*** | Tablas de aplicación/transaccionales | Usuarios, facturas, orgs |
| **dim_*** | Dimensiones (catálogo) | Canciones, artistas… |
| **fact_*** | Hechos/eventos | Reproducciones, búsquedas… |
| **agg_*** | Agregados precalculados | Dashboards rápidos |
| **ctl_*** | Control/metadatos de carga | Auditoría del pipeline |
| **Bronze / Silver / Gold** | Capas del pipeline | Crudo → limpio → listo para negocio |
| **Golden Path** | Camino feliz probado punta a punta | Demostrar que el flujo crítico funciona |
| **SMTP** | Protocolo de correo | Envío de emails (en lab suele ir a consola) |
| **i18n** | Internacionalización | ES/EN en la interfaz |

---

## 3. Mapa de módulos (todos)

Para cada módulo: significado, uso, menú, ruta, flujo, datos, acciones, relaciones, ejemplo, términos, estado.

### 3.1 Música / Inicio

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Inicio / Descubrir |
| **Qué es** | Pantalla principal del oyente |
| **Para qué** | Empezar a explorar el catálogo |
| **Quién** | Cualquier usuario autenticado |
| **Menú** | PERSONAL → Inicio (cuenta presentación) / Música → Inicio |
| **Ruta** | `/discover` |
| **Flujo** | Login → Inicio → play / buscar |
| **Datos** | Rails de descubrimiento, KPIs de catálogo (tracks/artistas/eventos) |
| **Acciones** | Reproducir, navegar a detalle |
| **Relación** | Catálogo warehouse + streaming |
| **Ejemplo** | Abrir Inicio y ver canciones sugeridas |
| **Términos** | catálogo, evento analítico |
| **Estado** | Funcional (catálogo importado) |

### 3.2 Playlists

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Listas / Playlists |
| **Ruta** | `/playlists` |
| **Para qué** | Crear y organizar colecciones propias |
| **Quién** | Oyentes |
| **Estado** | Funcional |

### 3.3 Favoritos

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Canciones que te gustan |
| **Ruta** | `/liked` |
| **Para qué** | Guardar likes |
| **Estado** | Funcional |

### 3.4 Historial

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Historial |
| **Ruta** | `/history` |
| **Para qué** | Ver qué escuchaste |
| **Estado** | Funcional |

### 3.5 Recomendaciones

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Recomendaciones |
| **Ruta** | `/recommendations` |
| **Para qué** | Sugerir música (incluye capas smart/AI según feature) |
| **Estado** | Funcional con componentes demo/académicos según motor |

### 3.6 Analítica musical

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Analítica / trending / comparativas / insights |
| **Rutas** | `/analytics`, `/trending`, `/comparatives`, `/insights/*`, `/dashboard` |
| **Para qué** | Entender comportamiento de escucha sobre el warehouse |
| **Estado** | Funcional (datos mayormente sintéticos derivados) |

### 3.7 Datos y ELT

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Pipeline ELT / Explorador |
| **Rutas** | `/elt-pipeline`, `/explorer` |
| **Para qué** | Ver cargas Bronze→Silver→Gold y explorar tablas |
| **Quién** | roles engineer/admin |
| **Estado** | Funcional (operación de laboratorio) |

### 3.8 Suscripciones personales (B2C)

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Plan personal / Planes personales / Facturación personal / Household |
| **Rutas** | `/account/subscription`, `/account/plans`, `/account/billing`, `/account/household` |
| **Para qué** | Cambiar de Free a Premium, facturar y compartir hogar |
| **Planes** | Free · Premium Individual · Premium Duo · Premium Familiar |
| **Estado** | Funcional + pagos **simulados** |

### 3.9 Households

| Campo | Contenido |
|-------|-----------|
| **Ruta** | `/account/household` |
| **Para qué** | Invitar miembros al plan Duo/Familiar |
| **Estado** | Funcional |

### 3.10 Organizaciones

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/organizations/*` |
| **Para qué** | Crear/gestionar la empresa, miembros, invitaciones, auditoría |
| **Estado** | Funcional |

### 3.11 CRM

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/crm/dashboard`, `/crm/prospects`, `/crm/opportunities`, `/crm/contacts`, `/crm/approvals`, `/crm/audit` |
| **Para qué** | Embudo comercial B2B |
| **Estado** | Funcional (datos demo etiquetados) |

### 3.12 Suscripciones empresariales (B2B)

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/subscriptions/overview`, `/subscriptions/plans`, `/subscriptions/trial` |
| **Planes** | Starter · Professional · Business · Enterprise |
| **Estado** | Funcional + trial/academia según plan |

### 3.13 Facturación / Pagos / Conciliación

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/billing/invoices`, `/billing/payment-attempts`, `/billing/reconciliation`, `/billing/refunds`, `/billing/credit-notes`, `/billing/ledger`, … |
| **Para qué** | Cobrar y cuadrar dinero (laboratorio) |
| **Estado** | Funcional · **pagos mock** |

### 3.14 Artistas empresariales / Catálogo / Lanzamientos / Derechos / Territorios / Usos / Conflictos

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/artist-profiles`, `/catalog-rights/assets`, `/catalog-rights/releases`, `/catalog-rights/contracts`, `/catalog-rights/conflicts` |
| **Para qué** | Gestionar catálogo empresarial y derechos (ámbito académico) |
| **Estado** | Funcional con etiquetas demo/sintéticas; **no es licencia legal real** |

### 3.15 Campañas

| Campo | Contenido |
|-------|-----------|
| **Ruta** | `/campaigns` |
| **Para qué** | Planificar y medir campañas |
| **Estado** | Funcional (demo seed) |

### 3.16 Analítica empresarial / KPI / Reportes / Decisiones

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/business-analytics`, `/business-analytics/kpis`, `/business-analytics/alerts`, `/reports`, `/business-decisions` |
| **Para qué** | Ver resultados B2B/B2C y decidir con evidencia |
| **Estado** | Funcional (mezcla métricas warehouse + app) |

### 3.17 Customer Success / Soporte

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/customer-success`, `/support` |
| **Para qué** | Salud del cliente y tickets |
| **Estado** | Funcional (datos demo) |

### 3.18 Privacidad / Cumplimiento

| Campo | Contenido |
|-------|-----------|
| **Rutas** | `/compliance`, `/compliance/admin` |
| **Para qué** | Privacidad y controles de cumplimiento |
| **Estado** | Funcional (capa académica) |

### 3.19 Operaciones de plataforma

| Campo | Contenido |
|-------|-----------|
| **Ruta** | `/platform-ops` |
| **Para qué** | Operar la plataforma a nivel global |
| **Quién** | platform admin / engineer |
| **Estado** | Funcional |

### 3.22 Distribución musical / portal artista (Spec 031)

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Distribución musical · Mi carrera |
| **Qué es** | Subir música en privado, revisión de catálogo, derechos y publicación |
| **Diferencia clave** | **Subir ≠ publicar**. Lo subido es privado hasta aprobación |
| **Quién** | `demo.artist`, artist_manager, catalog_reviewer, rights |
| **Rutas** | `/artist/*`, `/catalog-review/*` |
| **Media** | `data/media/private` y `data/media/published` · API `/api/v1/media/{id}/content` |
| **Audio** | Prioridad `local_published` en el resolutor |
| **Regalías** | Tras publicar + eventos válidos, Spec 030 puede atribuir |
| **Estado** | Funcional académico · sin distribución Spotify/Apple real |

---

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Regalías y pagos |
| **Qué es** | Fondos distribuibles, liquidaciones, estados de cuenta y payouts **simulados** |
| **Para qué** | Demostrar cómo un ingreso cobrado puede repartirse según contratos de derechos |
| **Quién** | Finance / billing_manager (gestión); artist_manager (consulta); `demo.business` (lectura) |
| **Menú** | FINANZAS / REGALÍAS Y PAGOS |
| **Rutas** | `/royalties`, `/royalties/pools`, `/royalties/settlements`, `/royalties/statements`, `/payouts` |
| **Flujo** | Pago settled → fuente → fondo aprobado → atribución → split contractual → settlement → payout simulado → statement |
| **Estado** | Funcional académico · **sin dinero real** · sin % universal |

---

## 4. Mapa de navegación completo

Árbol conceptual (roles típicos entre paréntesis):

```
Música
  → PRINCIPAL: Inicio /discover (todos)
  → MÚSICA: artistas, tracks, géneros, audio, search, playlists, liked, history (oyentes)
  → CUENTA PERSONAL: plan, planes, household, billing (oyentes)
  → RECOMENDACIONES: /recommendations (oyentes)

Analítica
  → ANALÍTICA musical: /analytics, /trending, /comparatives (oyentes+)
  → DATOS: ELT, explorer (engineer)

Clientes
  → CRM: dashboard, prospects, contacts, opportunities, approvals, audit (sales_*)
  → CS / Soporte (org + permisos)

Suscripciones y Finanzas
  → Suscripciones B2B: overview, plans, trial (org + subscription.*)
  → Billing: invoices, attempts, reconciliation, refunds… (billing.* / finance)

Gestión artística
  → Perfiles artista, catalog-rights, campaigns (org)

Dirección
  → Business analytics, reports, decisions (org)

Administración
  → Organizaciones, compliance, platform-ops, settings
```

### Tabla “qué demuestra”

| Módulo | Menú | Ruta | Rol principal | Qué demuestra |
|--------|------|------|---------------|---------------|
| Inicio | Personal/Música | `/discover` | oyente | Catálogo vivo |
| Plan personal | Personal | `/account/subscription` | oyente | Estado B2C |
| Planes personales | Personal | `/account/plans` | oyente | Free→Premium |
| Facturación personal | Personal | `/account/billing` | oyente | Factura B2C |
| Panel CRM | Ventas | `/crm/dashboard` | sales_manager | Embudo |
| Prospectos | Ventas | `/crm/prospects` | sales_manager | Lead gen |
| Oportunidades | Ventas | `/crm/opportunities` | sales_manager | Cierre |
| Estado org | Organización | `/organizations/.../settings` | member+ | Org activa |
| Plan org | Organización | `/subscriptions/overview` | billing/owner | B2B plan |
| Planes empresariales | Organización | `/subscriptions/plans` | billing/owner | Catálogo B2B |
| Facturas | Cobros | `/billing/invoices` | billing_manager | Ingresos |
| Intentos pago | Cobros | `/billing/payment-attempts` | billing_manager | Mock pay |
| Conciliación | Cobros | `/billing/reconciliation` | billing_manager | Cuadre |
| Panel empresarial | Resultados | `/business-analytics` | org viewer | Resultados |

---

## 5. Inventario técnico verificado (2026-07-14)

### Cómo se midió

| Métrica | Método |
|---------|--------|
| Specs | Carpetas `automation/specs/NNN-*` |
| Paquetes BE/FE | Directorios en `apps/backend/app/packages` y `apps/frontend/src/app/packages` |
| Endpoints | Decoradores `@*router.(get|post|put|patch|delete)` en `apps/backend/app/**/*.py` |
| Casos de uso | Métodos/funciones públicas en archivos `*use_cases*.py` (sin `_privados`) |
| Rutas FE | Literales `path:` en `*routes*.ts` |
| Tests BE | `apps/backend/tests/test_*.py` |
| Tests FE | `**/*.spec.ts` bajo frontend/src |
| Tamaño DuckDB | `os.path.getsize(data/warehouse/voxmetrik.duckdb)` |
| Filas catálogo/eventos | Inventario verificable en `.tmp_duckdb_inventory_out.txt` + evidencia Specs 014/016/017 (consulta live bloqueada por proceso Python PID 15808 al momentear) |
| Prefijos tabla | Regex de nombres `app_|dim_|fact_|agg_|ctl_` referenciados en backend |

### Cifras

| Ítem | Cantidad exacta | Nota |
|------|----------------:|------|
| Specs `001`…`029` | **29** | Primera `001-user-identity-access`, última `029-personal-music-subscriptions` |
| Paquetes backend | **22** | Ver lista abajo |
| Paquetes frontend | **22** | Ver lista abajo |
| Endpoints API (decoradores router) | **467** | Incluye paquetes + routers en raíz `app` (36) |
| Casos de uso públicos (`*use_cases*`) | **358** | 13 dominios con archivo use_cases; otros dominios usan services |
| Literales de ruta frontend | **110** | 15 archivos `*routes*.ts` |
| Tests backend | **86** | `test_*.py` top-level |
| Tests frontend | **24** | `*.spec.ts` |
| Tamaño DuckDB actual | **393.01 MB** | `voxmetrik.duckdb` |
| Canciones `dim_track` | **89 740** | Inventario warehouse |
| Artistas `dim_artista` | **31 429** | Inventario warehouse |
| Álbumes `dim_album` | **46 154** | Inventario warehouse |
| Eventos analíticos (suma ACTIVITY facts) | **900 000** | `synthetic_activity_target_900000` (ctl) |
| Tablas referenciadas por prefijo (código) | **app_ 149 · dim_ 8 · fact_ 10 · agg_ 29 · ctl_ 2** (+20 other); **218** nombres | Heurística estática |
| Filas inventariadas (snapshot) | dim\* **184 658** + fact\* **900 000** + agg\* **164 822** + app\* **4 899** + ctl\* **27** (+ raw_spotify 89 740) | `.tmp_duckdb_inventory_out.txt` |
| Golden Path artefacts | **3** archivos + tests asociados Spec 028/029 | Ver paths abajo |

**Paquetes backend (22):** ai, analytics, artists, billing, business_analytics, campaigns, catalog, catalog_rights, compliance, contracts, crm, customer_success, engagement, identity, organizations, personal_subscriptions, platform_ops, platform_rbac, reporting, streaming, subscriptions, users.

**Paquetes frontend (22):** administration, ai, analytics, artists, billing, business-analytics, campaigns, catalog-rights, compliance, crm, customer-success, data-engineering, history, organizations, personal-account, platform-ops, recommendations, reporting, smart, streaming, subscriptions, users.

### Endpoints por dominio (router)

| Dominio | Endpoints |
|---------|----------:|
| crm | 43 |
| billing | 39 |
| subscriptions | 32 |
| campaigns | 30 |
| catalog_rights | 29 |
| customer_success | 29 |
| analytics | 27 |
| compliance | 26 |
| catalog | 24 |
| reporting | 22 |
| platform_ops | 21 |
| artists | 19 |
| organizations | 19 |
| personal_subscriptions | 17 |
| business_analytics | 14 |
| engagement | 11 |
| identity | 11 |
| contracts | 10 |
| ai | 8 |
| _app_root | 36 |
| **Total** | **467** |

### Casos de uso por dominio (`*use_cases*`)

| Dominio | Casos de uso |
|---------|-------------:|
| crm | 42 |
| billing | 40 |
| subscriptions | 37 |
| campaigns | 32 |
| catalog_rights | 31 |
| compliance | 31 |
| customer_success | 31 |
| platform_ops | 26 |
| reporting | 24 |
| artists | 20 |
| personal_subscriptions | 17 |
| business_analytics | 17 |
| contracts | 10 |
| **Total** | **358** |

### Tabla resumen dominio

| Dominio | Paquetes | Casos de uso | Endpoints | Rutas FE (aprox. por área) | Tablas (prefijo típico) | Tests (área) |
|---------|----------|-------------:|----------:|----------------------------|-------------------------|--------------|
| Identity / users / orgs | identity, users, organizations, platform_rbac | (services + org/UC mixtos) | 11+19+… | organizations + auth | `app_user*`, `app_organization*` | tests identity/org |
| Streaming / catálogo | streaming, catalog, engagement, analytics | services | 24+11+27+… | music + insights | `dim_*`, `fact_*` | analytics/events |
| Personal subs | personal_subscriptions | 17 | 17 | `/account/*` (4) | `app_*` personal | Spec 029 tests |
| CRM / contracts | crm, contracts | 42+10 | 43+10 | `/crm/*` (14) | `app_crm_*` | Spec 017 |
| Subscriptions B2B | subscriptions | 37 | 32 | `/subscriptions/*` (9) | `app_subscription*` | Specs billing/subs |
| Billing | billing | 40 | 39 | `/billing/*` (10) | `app_invoice*`, payments | billing tests |
| Rights / artists / campaigns | catalog_rights, artists, campaigns | 31+20+32 | 29+19+30 | rights/artists/campaigns | `app_*` rights | Specs derechos |
| CS / compliance / ops / reporting / biz analytics | varios | 31+31+26+24+17 | … | CS, compliance, ops, reports, BA | `app_*` + KPIs | Specs 02x |

**Golden Paths:**
- `automation/specs/015-enterprise-business-foundation/business-golden-path.md`
- `automation/specs/028-enterprise-integration-and-final-validation/golden-path-validation.md`
- `apps/backend/tests/test_enterprise_golden_path_s028.py`
- (+ golden path personal en Spec 029)

---

## 6. Arquitectura

### Explicación sencilla

1. Tú abres la **web** (Angular).
2. La web habla con la **API** (FastAPI).
3. La API ejecuta **casos de uso** (reglas de negocio).
4. Los datos viven en **DuckDB**: tablas `app_*` (día a día) y warehouse (`dim_/fact_/agg_`).
5. Un **pipeline ELT** convierte datos crudos (Bronze) en limpios (Silver) y listos (Gold).
6. **RBAC** decide permisos. Cada organización está **aislada**.
7. **Pagos** y a veces **correo** están en modo laboratorio (mock / consola).

### Diagrama textual

```
Usuario
  → Frontend Angular
    → API FastAPI (endpoints)
      → Casos de uso / servicios (package-by-domain)
        → DuckDB (app_* + warehouse dim_/fact_/agg_/ctl_)
      ← respuesta JSON
    ← pantallas
```

### Técnica breve

- **Frontend:** Angular standalone components, i18n ES/EN, layout con nav por roles.
- **Backend:** FastAPI, paquetes por dominio.
- **DuckDB:** un archivo warehouse local (`data/warehouse/voxmetrik.duckdb`, **393.01 MB** al inventariar).
- **Separación app vs warehouse:** operativos vs analíticos.
- **Pipeline:** Bronze → Silver → Gold; control en `ctl_*`.
- **Datos:** catálogo importado (89 740 tracks); actividad sintética objetivo **900 000**.
- **Demo seed:** org + CRM + billing etiquetados `[SYNTHETIC]` / `(Demo)`.
- **SMTP:** configurable; en tests suele ser `console`.
- **RBAC + aislamiento org:** permisos por rol de plataforma y de organización.
- **Golden Paths:** tests punta a punta Spec 028/029.

---

## 7. Modelo de negocio

### B2C

| Plan | Idea | Beneficios (producto) | Cobro |
|------|------|------------------------|-------|
| **Free** | Entrar sin pagar | Acceso básico a exploración | Sin cargo |
| **Premium Individual** | Una persona paga | Entitlements premium (límites/features del plan) | Factura personal + pago mock |
| **Premium Duo** | Dos personas | Household reducido | Idem |
| **Premium Familiar** | Familia | Más miembros en household | Idem |

**Factura personal** = documento B2C. **Pago simulado** = confirma la factura en laboratorio.

### B2B

| Plan | Idea | Capacidades típicas de producto |
|------|------|----------------------------------|
| **Starter** | Entrada pequeña | Base org + módulos limitados |
| **Professional** | Operación comercial | CRM + suscripción org (demo canónico) |
| **Business** | Escala | Más seats/capacidades según catálogo |
| **Enterprise** | Gran cuenta | Capacidades avanzadas (SSO/SLA pueden ser académicas) |

**Organización** tiene **miembros** con roles. **Factura empresarial** y **pago mock** cierran el MRR B2B.

### Ventajas reales (no genéricas)

- Un solo sistema muestra **ingreso consumidor + ingreso empresa**.
- El catálogo musical **importado** da credibilidad visual.
- Los **900 000 eventos** permiten dashboards sin esperar tráfico real.
- El menú de `demo.business` evita distracciones técnicas en la defensa.

---

## 8. Cuenta `demo.business` (presentación)

| Campo | Valor |
|-------|-------|
| Usuario | `demo.business` |
| Email | `demo.business@demo.voxmetriks.local` |
| Contraseña | Variable de entorno `DEMO_ACCOUNT_PASSWORD` (nunca documentar el valor) |
| Verificada | Sí (`email_verified`) |
| Org | **VOXMETRIKS Demo** |
| Roles | plataforma `sales_manager` + org `billing_manager` |
| Preferencia UI | `presentation_nav=true` (solo menú; **no borra rutas**) |
| Plan personal | Premium Individual (mock) |

### Menú visible

```
PERSONAL
  - Inicio                    /discover
  - Plan personal             /account/subscription
  - Planes personales         /account/plans
  - Facturación personal      /account/billing

VENTAS
  - Panel CRM                 /crm/dashboard
  - Prospectos                /crm/prospects
  - Oportunidades             /crm/opportunities

ORGANIZACIÓN
  - Estado de organización    /organizations/{id}/settings  (o /organizations/none)
  - Plan de la organización   /subscriptions/overview
  - Planes empresariales      /subscriptions/plans

COBROS
  - Facturas                  /billing/invoices
  - Intentos de pago          /billing/payment-attempts
  - Conciliación              /billing/reconciliation

RESULTADOS
  - Panel empresarial         /business-analytics
```

### Qué NO se muestra (pero el sistema sigue existiendo)

ELT, exploradores, auditorías, artistas/derechos/conflictos/campañas, CS, soporte, cumplimiento, ops, administración global, household, approvals CRM, refunds/ledger en menú, KPIs/alerts BA.

### Qué puede / no puede

| Puede | No puede (sin roles peligrosos) |
|-------|----------------------------------|
| Ver planes B2C/B2B, CRM básico, facturas, intentos, conciliación, panel BA | Cerrar org como owner, platform ops globales, administrar compliance como admin |

Otras cuentas **conservan el menú completo**.

---

## 9. Documentos hermanos

- `docs/GUIA-PRESENTACION-NEGOCIO.md` — guion ≤7 minutos
- `docs/RESUMEN-RAPIDO-PRESENTACION.md` — hoja de una mirada
- `docs/DEMO-ACCOUNTS.md` — cuentas demo (sin contraseñas)

---

## 10. Confirmaciones

- No se crearon Specs nuevas.
- No se eliminaron módulos, rutas, endpoints ni datos.
- No se cambiaron reglas de negocio.
- No se ejecutó Git en esta entrega documental/código de presentación.
