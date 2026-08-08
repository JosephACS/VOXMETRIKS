> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Feature Specification: Identidad y Acceso Operativo de Usuario

**Feature Branch**: `001-user-identity-access`  
**Feature Directory**: `specs/001-user-identity-access/`  
**Created**: 2026-06-19  
**Status**: Draft — Pending `/speckit-plan`  
**Input**: Primera especificación operativa formal de Voxmetriks: capacidad de negocio fundacional para registro, autenticación, gestión de perfil, control de acceso y persistencia de identidad de usuario.

---

## Contexto Empresarial

Voxmetriks es una plataforma empresarial que combina experiencia de consumo musical con analítica de catálogo y personalización de usuario (Constitución v1.0.0 §1–§2). Para que un usuario final **opere** la plataforma de forma personalizada — guardar favoritos, crear playlists, recibir recomendaciones, acceder a su perfil y, cuando corresponda, a funciones de ingeniería de datos — el sistema MUST establecer **quién es el usuario**, **validar su identidad** y **aplicar reglas de acceso** antes de permitir operaciones sobre datos de aplicación.

La auditoría arquitectónica confirmó que módulos operativos dependientes (playlists, favoritos, recomendaciones personalizadas, perfil, rutas protegidas del frontend) **requieren identidad de usuario autenticada**, mientras que el catálogo musical y analytics generales permanecen accesibles sin identidad. Por tanto, la **Identidad y Acceso Operativo de Usuario** constituye el **módulo operativo fundacional** sobre el cual se construyen todas las demás capacidades personalizadas del nivel operativo.

Esta especificación documenta la capacidad de negocio en términos de valor para el usuario y reglas del dominio, independientemente de detalles de implementación actual. Describe el comportamiento **requerido** del sistema como producto operativo, alineado con la Constitución ratificada.

---

## Problema

### Situación actual

Los usuarios de Voxmetriks necesitan una identidad persistente dentro de la plataforma para:

1. **Acceder** a la aplicación web más allá de la navegación anónima de catálogo.
2. **Mantener** preferencias personales (género favorito, modo oscuro, privacidad, calidad de audio).
3. **Operar** biblioteca personal (playlists, favoritos) sin mezclar datos con otros usuarios.
4. **Diferenciar** permisos entre usuario estándar y roles con acceso a operaciones de data engineering.

Sin una capacidad operativa formalmente especificada de identidad y acceso:

- No existe trazabilidad empresarial desde objetivos estratégicos hasta historias de usuario del dominio `users`.
- Las reglas de negocio de autenticación y autorización están implícitas en código, no gobernadas por SDD.
- Features futuras (playlists, recomendaciones, settings) carecen de fundamento documentado de dependencia.
- Riesgos operativos (sesiones expiradas, credenciales duplicadas, acceso no autorizado a rutas) no tienen criterios de aceptación unificados.

### Problema de negocio

**Los usuarios finales no pueden confiar en un marco operativo unificado** que garantice identidad, persistencia de perfil y control de acceso coherente en todo el ciclo de vida de su relación con Voxmetriks — desde el registro hasta la gestión diaria de preferencias y el acceso a funcionalidades restringidas.

---

## Objetivo

Establecer y gobernar la **capacidad operativa de Identidad y Acceso de Usuario** en Voxmetriks, definiendo:

1. Cómo un **nuevo usuario** crea una cuenta y obtiene acceso autenticado.
2. Cómo un **usuario existente** inicia sesión y mantiene su sesión activa según preferencias de duración.
3. Cómo el **usuario autenticado** consulta y actualiza su perfil y preferencias operativas.
4. Cómo el **sistema** persiste identidad, sesiones y preferencias de forma aislada por usuario.
5. Cómo el **sistema** controla el acceso a funcionalidades operativas según estado de autenticación y rol.
6. Cómo un **usuario** cierra su sesión en el cliente, terminando el uso de credenciales locales.

**Resultado esperado:** cualquier actor operativo (usuario final, administrador de plataforma, analista con rol engineer) puede completar su ciclo de identidad de forma predecible, medible y trazable a objetivos empresariales.

---

## Trazabilidad Empresarial

### Cadena oficial (Constitución v1.0.0 §12)

| ID | Eslabón | Descripción |
|----|---------|-------------|
| **OE-01** | Objetivo Estratégico | Convertir Voxmetriks en plataforma de referencia que unifica experiencia musical personalizada con analítica de datos gobernada |
| **OT-01** | Objetivo Táctico | Habilitar identidad de usuario y modelo de acceso como prerrequisito de personalización y operaciones de biblioteca personal |
| **OO-01** | Objetivo Operativo | Operar ciclo completo registro → autenticación → perfil → control de acceso → persistencia para usuarios finales y roles privilegiados |
| **M-01** | Meta | 100% de operaciones sobre biblioteca personal (playlists, favoritos) ejecutables únicamente con identidad autenticada válida |
| **M-02** | Meta | 95% de intentos de login/registro completados exitosamente en primer intento con datos válidos |
| **M-03** | Meta | 100% de rutas operativas restringidas bloqueadas para usuarios no autenticados |
| **DEP-01** | Departamento | **Plataforma de Producto** (dominio Users / Identity) |
| **PKG-01** | Paquete | `users` (backend `packages/users/`, frontend `packages/users/`, `core/auth`) |



## Matriz CU → HU → FR → CA

Subconjunto de [`TRACEABILITY-MASTER.md`](../README.md) (Constitución §12).

| CU | HU | FR | CA |
|----|----|----|-----|
| CU-01 | US-01 | FR-001 | CA-001 |
| CU-01 | US-01 | FR-002 | CA-001 |
| CU-01 | US-01 | FR-003 | CA-001 |
| CU-01 | US-01 | FR-004 | CA-008 |
| CU-01 | US-01 | FR-017 | CA-001 |
| CU-01 | US-01 | FR-018 | CA-001 |
| CU-02 | US-02 | FR-005 | CA-002 |
| CU-02 | US-02 | FR-006 | CA-002 |
| CU-02 | US-02 | FR-007 | CA-002 |
| CU-02 | US-02 | FR-020 | CA-002 |
| CU-03 | US-03 | FR-008 | CA-003 |
| CU-03 | US-03 | FR-009 | CA-003 |
| CU-04 | US-04 | FR-010 | CA-004 |
| CU-04 | US-04 | FR-011 | CA-004 |
| CU-05 | US-05 | FR-012 | CA-005 |
| CU-06 | US-06 | FR-013 | CA-006 |
| CU-06 | US-06 | FR-014 | CA-006 |
| CU-06 | US-07 | FR-015 | CA-007 |
| CU-07 | US-01 | FR-016 | CA-001 |
| CU-07 | US-02 | FR-016 | CA-002 |
| CU-07 | US-02 | FR-019 | CA-002 |
| CU-07 | US-06 | FR-019 | CA-006 |

### Matriz de trazabilidad (granular)

| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |
|----|----|----|------|------|---------|----|----|------|------|
| OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-01 | US-01 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-02 | US-02 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-01 | DEP-01 | PKG-01 | CU-03 | US-03 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-04 | US-04 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-05 | US-05 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-06 | US-06 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-06 | US-07 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-01 | DEP-01 | PKG-01 | CU-07 | US-01 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-01 | DEP-01 | PKG-01 | CU-07 | US-02 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-02 | DEP-01 | PKG-01 | CU-07 | US-02 | 001 | Pendiente |
| OE-01 | OT-01 | OO-01 | M-03 | DEP-01 | PKG-01 | CU-07 | US-06 | 001 | Pendiente |
## Actores

| Actor | Descripción | Interés |
|-------|-------------|---------|
| **Usuario Visitante** | Persona sin cuenta ni sesión activa | Explorar catálogo; decidir registrarse o iniciar sesión |
| **Usuario Registrado** | Persona con cuenta activa y sesión válida | Acceder a funcionalidades personalizadas y gestionar perfil |
| **Usuario Administrador / Engineer** | Usuario registrado con rol privilegiado para operaciones de data engineering | Acceder a pipeline ELT y explorador de warehouse además de funciones estándar |
| **Sistema Voxmetriks** | Plataforma como conjunto backend + frontend + persistencia | Validar identidad, aplicar reglas, persistir datos de aplicación por usuario |
| **Operador de Plataforma** | Responsable de disponibilidad del servicio de identidad | Monitorear salud del subsistema; no actor directo de casos de uso UI |

---

## Casos de Uso

### CU-01: Registrar cuenta de usuario

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-01 |
| **Actor principal** | Usuario Visitante |
| **Precondición** | Visitante accede a pantalla de registro; no tiene sesión activa |
| **Flujo principal** | 1. Visitante ingresa username, email, password y opcionalmente género favorito → 2. Sistema valida unicidad y reglas → 3. Sistema crea identidad persistente → 4. Sistema inicia sesión automáticamente → 5. Visitante accede como Usuario Registrado |
| **Postcondición** | Cuenta existe; sesión activa; usuario redirigido a área autenticada |
| **Flujo alternativo** | 2a. Email o username duplicado → mensaje de error claro, sin crear cuenta |
| **Reglas de negocio** | RB-001, RB-002, RB-003, RB-004 |

### CU-02: Iniciar sesión

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-02 |
| **Actor principal** | Usuario Visitante o Usuario Registrado (sesión expirada) |
| **Precondición** | Cuenta existente; no hay sesión válida |
| **Flujo principal** | 1. Usuario ingresa identificador (email o username) y password → 2. Sistema valida credenciales → 3. Sistema emite sesión con duración según "recordarme" → 4. Usuario accede a área autenticada |
| **Postcondición** | Sesión activa; token/credencial de sesión disponible para operaciones |
| **Flujo alternativo** | 2a. Credenciales inválidas → error genérico sin revelar si email existe |
| **Reglas de negocio** | RB-005, RB-006, RB-007 |

### CU-03: Consultar perfil del usuario autenticado

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-03 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Usuario solicita su perfil → 2. Sistema retorna identidad, plan, preferencias, estadísticas resumidas de biblioteca personal |
| **Postcondición** | Usuario visualiza datos actualizados de su identidad operativa |
| **Reglas de negocio** | RB-008, RB-009 |

### CU-04: Actualizar preferencias de perfil

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-04 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Sesión válida |
| **Flujo principal** | 1. Usuario modifica preferencias (tema, calidad audio, recomendaciones, privacidad, género favorito) → 2. Sistema persiste cambios → 3. Sistema confirma perfil actualizado |
| **Postcondición** | Preferencias persistidas; visibles en consultas posteriores |
| **Reglas de negocio** | RB-010, RB-011 |

### CU-05: Cerrar sesión

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-05 |
| **Actor principal** | Usuario Registrado |
| **Precondición** | Sesión activa en cliente |
| **Flujo principal** | 1. Usuario solicita logout → 2. Cliente elimina credenciales locales → 3. Usuario queda como Visitante en UI |
| **Postcondición** | Cliente no envía credenciales; rutas protegidas inaccesibles |
| **Nota** | Invalidación server-side de sesión es mejora futura; logout cliente es mínimo operativo |
| **Reglas de negocio** | RB-012 |

### CU-06: Control de acceso a funcionalidades operativas

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-06 |
| **Actor principal** | Sistema Voxmetriks |
| **Precondición** | Usuario intenta acceder a ruta o operación clasificada |
| **Flujo principal** | 1. Sistema evalúa clasificación del recurso → 2. Si requiere auth y no hay sesión → redirige a login → 3. Si requiere rol engineer y usuario no lo tiene → deniega acceso |
| **Postcondición** | Solo usuarios autorizados ejecutan operaciones restringidas |
| **Reglas de negocio** | RB-013, RB-014, RB-015 |

### CU-07: Persistir identidad y sesiones de usuario

| Campo | Descripción |
|-------|-------------|
| **ID** | CU-07 |
| **Actor principal** | Sistema Voxmetriks |
| **Precondición** | Operación de registro, login o actualización de perfil |
| **Flujo principal** | 1. Sistema almacena identidad en capa de aplicación → 2. Sistema almacena sesión con expiración → 3. Datos aislados por user_id |
| **Postcondición** | Identidad sobrevive reinicios; sesiones respetan expiración |
| **Reglas de negocio** | RB-016, RB-017 (Constitución P6: separación warehouse vs app) |

---

## User Scenarios & Testing *(mandatory)*

### User Story US-01 — Registro de nueva cuenta (Priority: P1)

Como **Usuario Visitante**, quiero **crear una cuenta con username, email y contraseña**, para **acceder a funcionalidades personalizadas de Voxmetriks** (playlists, favoritos, perfil).

**Why this priority**: Sin registro no existe identidad persistente; es el punto de entrada operativo del ciclo de vida del usuario. Todas las capacidades personalizadas dependen de este flujo.

**Independent Test**: Registrar un usuario nuevo con datos válidos y verificar acceso inmediato al dashboard autenticado sin intervención manual adicional.

**Acceptance Scenarios**:

1. **Given** un visitante en la pantalla de registro, **When** ingresa username (≥3 caracteres), email válido único y password (≥4 caracteres), **Then** el sistema crea la cuenta, inicia sesión automáticamente y redirige al área autenticada.
2. **Given** un email ya registrado, **When** el visitante intenta registrarse con el mismo email, **Then** el sistema rechaza la operación con mensaje claro y no crea cuenta duplicada.
3. **Given** un username ya registrado, **When** el visitante intenta registrarse, **Then** el sistema rechaza con mensaje de duplicidad.
4. **Given** registro exitoso, **When** el sistema crea la cuenta, **Then** el usuario recibe plan inicial "Free" y preferencias por defecto (modo oscuro, calidad alta, recomendaciones habilitadas, privacidad no pública).

**Maps to**: CU-01 | FR-001, FR-002, FR-003, FR-004 | M-02

---

### User Story US-02 — Inicio de sesión (Priority: P1)

Como **Usuario Visitante** con cuenta existente, quiero **iniciar sesión con email o username y contraseña**, para **retomar mi experiencia personalizada**.

**Why this priority**: Paridad con registro como entrada operativa; usuarios recurrentes constituyen la mayoría del uso operativo diario.

**Independent Test**: Login con credenciales válidas de usuario existente; verificar acceso a dashboard y token de sesión activo.

**Acceptance Scenarios**:

1. **Given** cuenta existente, **When** usuario ingresa email y password correctos, **Then** sistema autentica y concede acceso al área protegida.
2. **Given** cuenta existente, **When** usuario ingresa username y password correctos, **Then** sistema autentica igual que con email.
3. **Given** credenciales incorrectas, **When** usuario intenta login, **Then** sistema responde con error de autenticación sin indicar cuál campo falló.
4. **Given** opción "recordarme" activada, **When** login exitoso, **Then** sesión persiste en almacenamiento durable del cliente por duración extendida (90 días operativos).
5. **Given** opción "recordarme" desactivada, **When** login exitoso, **Then** sesión usa almacenamiento de sesión con duración corta (1 día operativo).

**Maps to**: CU-02 | FR-005, FR-006, FR-007 | M-02

---

### User Story US-03 — Consulta de perfil autenticado (Priority: P1)

Como **Usuario Registrado**, quiero **ver mi perfil completo** (identidad, plan, preferencias, resumen de biblioteca), para **entender mi estado operativo en la plataforma**.

**Why this priority**: El perfil es el centro de operaciones del usuario; consolida identidad y métricas personales necesarias para CU-04 y navegación consciente.

**Independent Test**: Usuario autenticado solicita perfil; recibe datos coherentes con su cuenta sin exponer password ni datos de otros usuarios.

**Acceptance Scenarios**:

1. **Given** sesión válida, **When** usuario accede a su perfil, **Then** sistema retorna username, email, plan, género favorito, preferencias y estadísticas (conteo favoritos, playlists).
2. **Given** sesión inválida o ausente, **When** usuario solicita perfil, **Then** sistema deniega acceso (no autenticado).
3. **Given** perfil consultado, **When** sistema responde, **Then** no incluye password ni hash de password.

**Maps to**: CU-03 | US-03 | FR-008, FR-009 | CA-003 | M-01

*Delimitación spec 006:* CU-03/US-03 gobiernan **contrato API** de perfil; la UX en `/users` se especifica en **006** (US-PF01).

---

### User Story US-04 — Actualización de preferencias (Priority: P2)

Como **Usuario Registrado**, quiero **modificar mis preferencias operativas** (tema, calidad de audio, recomendaciones, privacidad, género favorito), para **adaptar Voxmetriks a mi forma de uso**.

**Why this priority**: Complementa perfil; no bloquea MVP operativo (registro/login/perfil lectura) pero es esencial para experiencia personalizada completa.

**Independent Test**: PATCH preferencias parciales; verificar persistencia en consulta posterior de perfil.

**Acceptance Scenarios**:

1. **Given** sesión válida, **When** usuario actualiza una o más preferencias permitidas, **Then** sistema persiste solo campos enviados y retorna perfil actualizado.
2. **Given** actualización parcial, **When** usuario no envía un campo, **Then** valor previo se mantiene sin cambios.
3. **Given** sesión inválida, **When** intento de actualización, **Then** sistema deniega operación.

**Maps to**: CU-04 | US-04 | FR-010, FR-011 | CA-004 | M-02

*Delimitación spec 006:* CU-04/US-04 gobiernan **PATCH API**; toggles UX en `/settings` se especifican en **006** (US-ST02).

---

### User Story US-05 — Cierre de sesión (Priority: P2)

Como **Usuario Registrado**, quiero **cerrar sesión**, para **terminar mi acceso autenticado en el dispositivo actual**.

**Why this priority**: Control operativo básico de seguridad del lado cliente; necesario antes de compartir dispositivo o cambiar de cuenta.

**Independent Test**: Logout elimina token del cliente; navegación a rutas protegidas redirige a login.

**Acceptance Scenarios**:

1. **Given** sesión activa, **When** usuario ejecuta logout, **Then** cliente elimina token y datos de usuario almacenados localmente.
2. **Given** logout completado, **When** usuario intenta acceder a dashboard, **Then** sistema redirige a login.

**Maps to**: CU-05 | FR-012 | M-03

---

### User Story US-06 — Protección de rutas y operaciones (Priority: P1)

Como **Sistema Voxmetriks**, debo **impedir acceso a funcionalidades operativas personalizadas sin autenticación**, para **garantizar aislamiento de biblioteca personal por usuario**.

**Why this priority**: Sin control de acceso, M-01 y M-03 no se cumplen; playlists/favoritos perderían significado operativo.

**Independent Test**: Acceso directo a URL protegida sin token → redirección login; acceso con token válido → permitido.

**Acceptance Scenarios**:

1. **Given** visitante sin sesión, **When** navega a dashboard, playlists, favoritos, settings o perfil, **Then** sistema redirige a login.
2. **Given** visitante sin sesión, **When** navega a catálogo público (artists, tracks, analytics generales), **Then** acceso permitido.
3. **Given** usuario autenticado, **When** navega a rutas protegidas, **Then** acceso concedido.
4. **Given** visitante autenticado en login page, **When** ya tiene sesión, **Then** redirige a dashboard (guest guard).

**Maps to**: CU-06 | FR-013, FR-014 | M-03

---

### User Story US-07 — Acceso por rol Engineer (Priority: P3)

Como **Usuario Administrador/Engineer**, quiero **acceder a funcionalidades de data engineering** (pipeline ELT, explorador warehouse), para **operar la plataforma de datos sin confundir permisos con usuarios estándar**.

**Why this priority**: Rol operativo especializado; depende de identidad base (P1–P2) ya establecida.

**Independent Test**: Usuario admin autenticado ve tabs ELT/Explorer; usuario estándar no.

**Acceptance Scenarios**:

1. **Given** usuario con rol engineer (username admin o email admin@*), **When** accede al shell autenticado, **Then** ve opciones de pipeline ELT y warehouse explorer.
2. **Given** usuario estándar autenticado, **When** accede al shell, **Then** no ve opciones de data engineering.
3. **Given** visitante, **When** intenta acceder directamente a rutas ELT/explorer, **Then** redirige a login primero; si login estándar, rutas accesibles pero UI oculta funciones engineer.

**Maps to**: CU-06 | FR-015 | M-03

---

### Edge Cases

- **Sesión expirada server-side**: Usuario con token en cliente pero sesión expirada en servidor → operaciones protegidas fallan con no autenticado; cliente SHOULD redirigir a login en error 401.
- **Username/email con mayúsculas**: Comparación case-insensitive para email y username en login/registro.
- **Password en límite mínimo**: Exactamente 4 caracteres → aceptado; 3 → rechazado con mensaje claro.
- **Preferencias JSON corruptas**: Sistema trata como objeto vacío y permite reescritura sin crash.
- **Registro concurrente mismo email**: Solo una cuenta creada; segunda operación falla por unicidad.
- **Logout sin conectividad**: Logout cliente MUST funcionar offline (elimina storage local).
- **Múltiples sesiones**: Usuario puede tener múltiples tokens activos (dispositivos); no se requiere invalidación cruzada en v1 operativa.
- **Usuario demo en entorno development**: Cuentas precargadas permitidas solo en entorno no productivo (Constitución §23.4).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow visitors to register with username, email, password, and optional favorite genre.
- **FR-002**: System MUST enforce username minimum length of 3 characters at registration.
- **FR-003**: System MUST enforce password minimum length of 4 characters at registration.
- **FR-004**: System MUST reject registration when email or username already exists in persistent user store.
- **FR-005**: System MUST authenticate users by email **or** username plus password.
- **FR-006**: System MUST issue a session credential upon successful registration or login.
- **FR-007**: System MUST support extended session duration when user selects "remember me" and short duration otherwise.
- **FR-008**: System MUST provide authenticated users a profile view with identity, plan, preferences, and summary library stats.
- **FR-009**: System MUST deny profile access to unauthenticated requests.
- **FR-010**: System MUST allow authenticated users to update operational preferences: dark mode, audio quality, recommendations enabled, privacy public flag, favorite genre.
- **FR-011**: System MUST persist preference updates partially (unspecified fields retain previous values).
- **FR-012**: Client MUST allow users to logout by clearing local session credentials.
- **FR-013**: System MUST restrict personalized operational routes (dashboard, playlists, favorites, profile, settings) to authenticated users.
- **FR-014**: System MUST allow unauthenticated access to public catalog and general analytics routes per product classification.
- **FR-015**: System MUST differentiate engineer role access to data engineering UI from standard users based on identity attributes (admin username or admin@ email pattern).
- **FR-016**: System MUST persist user identity and sessions in application data layer, isolated per user_id (not warehouse ELT tables).
- **FR-017**: System MUST assign default plan "Free" and default preferences on registration.
- **FR-018**: System MUST auto-login user immediately after successful registration.
- **FR-019**: System MUST attach session credential to subsequent authenticated operational requests from client.
- **FR-020**: System MUST return generic authentication failure message without revealing whether identifier exists.

### Non-Functional Requirements

- **NFR-001 (Availability)**: Identity operations (login, register) MUST remain available when warehouse analítico está poblado y API en ejecución.
- **NFR-002 (Response time)**: Login and registration MUST complete within 3 seconds p95 under normal dev/staging load.
- **NFR-003 (Usability)**: Registration and login forms MUST display field-level validation errors understandable to non-technical users.
- **NFR-004 (Security — operational)**: Profile responses MUST NOT expose password or password hash.
- **NFR-005 (Security — operational)**: Session credentials MUST NOT be logged in application logs.
- **NFR-006 (Privacy)**: User preferences include privacy_public flag governing visibility preferences; defaults MUST be non-public.
- **NFR-007 (Reliability)**: User identity MUST survive API restart (persistent store, not in-memory only).
- **NFR-008 (i18n)**: Auth UI strings MUST support ES/EN via platform i18n service.
- **NFR-009 (Accessibility — target)**: Login/register forms SHOULD be operable via keyboard navigation.
- **NFR-010 (Auditability)**: Feature MUST maintain traceability matrix OE→HU documented in this spec.

### Reglas de Negocio

| ID | Regla |
|----|-------|
| **RB-001** | Username MUST be unique en toda la plataforma (case-insensitive comparison). |
| **RB-002** | Email MUST be unique en toda la plataforma (case-insensitive). |
| **RB-003** | Username MUST have minimum 3 characters. |
| **RB-004** | Password MUST have minimum 4 characters at registration. |
| **RB-005** | Login identifier MAY be email OR username interchangeably. |
| **RB-006** | Failed login MUST NOT disclose whether identifier or password was wrong. |
| **RB-007** | Session duration: 90 días operativos si "recordarme"; 1 día si no. |
| **RB-008** | Profile MUST include: id, username, email, plan, favorite_genre, preferences, created_at. |
| **RB-009** | Profile stats MUST summarize favorites_count and playlists_count del usuario autenticado únicamente. |
| **RB-010** | Preferencias válidas: dark_mode (bool), audio_quality (enum: high/normal/low), recommendations_enabled (bool), privacy_public (bool). |
| **RB-011** | favorite_genre MAY update via preferences endpoint. |
| **RB-012** | Logout cliente MUST clear all local auth storage (localStorage and sessionStorage). |
| **RB-013** | Rutas operativas personalizadas REQUIRE authentication. |
| **RB-014** | Rutas catálogo/analytics generales ALLOW anonymous access. |
| **RB-015** | Engineer UI visible ONLY for admin username OR email starting with admin@. |
| **RB-016** | User identity MUST persist in application layer (`app_user`), NOT in warehouse ELT dimensions. |
| **RB-017** | Sessions MUST persist in application layer (`app_session`) with expires_at enforcement server-side. |
| **RB-018** | New users MUST start on plan "Free" unless business rule extended in future spec. |
| **RB-019** | Demo accounts (demo, admin) MAY exist ONLY in non-production environments. |

### Key Entities

- **User (Identidad)**: Representa una persona registrada. Atributos: identificador único, username, email, plan de suscripción operativo, género favorito, fecha creación, preferencias. Relación 1:N con Session y biblioteca personal.

- **Session (Sesión)**: Representa una autenticación activa. Atributos: token opaco, referencia a User, fechas creación/expiración. Habilita operaciones autenticadas hasta expiración.

- **UserPreferences (Preferencias)**: Sub-documento de User. Atributos operativos de experiencia: tema, calidad audio, recomendaciones, privacidad. Mutable post-registro.

- **Role (Rol operativo)**: Clasificación derivada de atributos de User (standard | engineer). No entidad persistida separada en v1; regla de negocio RB-015.

- **UserLibraryStats (Estadísticas resumen)**: Vista derivada: conteos de favoritos y playlists del usuario. Solo lectura en perfil.

---

## Criterios de Aceptación Globales (Feature)

La feature **001-user-identity-access** se considera **aceptada operativamente** cuando:

1. **CA-001**: Un visitante puede registrarse, quedar autenticado y acceder al dashboard en un solo flujo.
2. **CA-002**: Un usuario existente puede login con email o username.
3. **CA-003**: Usuario autenticado consulta perfil con stats personales sin datos de otros usuarios.
4. **CA-004**: Usuario autenticado actualiza al menos una preferencia y persiste tras recargar.
5. **CA-005**: Logout impide acceso a rutas protegidas sin re-login.
6. **CA-006**: Visitante anónimo accede a catálogo pero no a playlists/favoritos/dashboard.
7. **CA-007**: Usuario admin ve funciones engineer; usuario estándar no.
8. **CA-008**: Registro duplicado rechazado con mensaje comprensible.
9. **CA-009**: Sesión expirada server-side produce comportamiento no autenticado en operaciones protegidas.
10. **CA-010**: Matriz de trazabilidad OE→HU completa y vinculada en spec.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% de registros con datos válidos completan en ≤ 30 segundos desde apertura de formulario hasta dashboard.
- **SC-002**: 95% de logins con credenciales válidas completan en ≤ 10 segundos.
- **SC-003**: 100% de intentos de acceso a playlists/favoritos sin sesión resultan en redirección a login.
- **SC-004**: 100% de respuestas de perfil omiten campos de password/hash en verificación automatizada.
- **SC-005**: 90% de usuarios completan registro o login en primer intento (datos válidos, entorno estable).
- **SC-006**: 0 casos de datos de biblioteca personal de un usuario visibles en perfil de otro en pruebas de aislamiento.

---

## Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R-001 | Sesión cliente válida pero expirada en servidor confunde al usuario | Media | Medio | Interceptor 401 → logout + redirect login |
| R-002 | Credenciales demo en producción | Baja | Alto | RB-019; Constitución §23.4 |
| R-003 | Confusión warehouse vs app data en implementaciones futuras | Media | Alto | FR-016, RB-016; Constitution P6 |
| R-004 | Rol engineer hardcoded (admin@) no escalable | Media | Medio | Spec futura RBAC formal; documentado como v1 |
| R-005 | Logout solo cliente deja sesión server-side activa | Alta | Bajo | Aceptado v1; spec futura server logout |
| R-006 | Requisitos de seguridad avanzados (OAuth, MFA) fuera de alcance malinterpretados | Media | Medio | Alcance explícito §Out of Scope |
| R-007 | Dependencia playlists/favorites no disponibles degradan perfil | Baja | Bajo | Stats retornan 0 si vacío |

---

## Dependencias

### Dependencias internas (runtime)

| Dependencia | Tipo | Descripción |
|-------------|------|-------------|
| API Voxmetriks operativa | Hard | Endpoints de identidad deben estar desplegados |
| Persistencia application layer | Hard | Tablas de identidad y sesión inicializadas en startup |
| Frontend auth shell | Hard | Guards, interceptors, login page |
| Módulo playlists | Soft | Stats de perfil enriquecen con conteo playlists |
| Módulo favorites | Soft | Stats de perfil enriquecen con conteo favoritos |

### Dependencias de gobernanza

| Dependencia | Descripción |
|-------------|-------------|
| Constitución v1.0.0 | Principios P2, P6, P8, P9, P11 |
| Spec Kit workflow | Plan/tasks posteriores vía `/speckit-plan` |
| `.specify/feature.json` | Pointer a este directorio |

### Dependencias externas

| Dependencia | Descripción |
|-------------|-------------|
| Ninguna identidad externa | No SSO/OAuth en alcance v1 operativa |

---

## Relación con la Constitución v1.0.0

| Principio / Sección | Aplicación en esta feature |
|---------------------|----------------------------|
| **§4.3 Nivel Operativo** | Feature fundacional del nivel operativo — ciclo diario usuario |
| **§5 P2 Package-by-Domain** | Dominio `users` exclusivo |
| **§5 P6 Warehouse vs App** | FR-016, RB-016: identidad en `app_*`, no ELT |
| **§5 P8 SDD** | Primera spec formal en `specs/` |
| **§5 P9 Contract-First** | Plan futuro alineará OpenAPI + api.models.ts |
| **§5 P11 Security Target** | NFR-004/005 operativos; hardening criptográfico fuera de alcance |
| **§12 Trazabilidad** | Matriz OE→Impl completa |
| **§14 Nomenclatura** | Branch `001-user-identity-access` |
| **§15 Reglas Specs** | Spec operativa, no deuda técnica |
| **§18 Seguridad** | RB-006, NFR-004; TD-004 no es objetivo de esta spec |
| **§19 APIs** | Dominio `/users` — 4 endpoints base del alcance |

---

## Out of Scope

- Remediación de algoritmo de hashing (TD-004) — spec futura security-hardening
- OAuth2 / SSO / JWT externo
- Recuperación de password / email verification
- Invalidación server-side de sesión en logout (v1)
- RBAC formal multi-rol más allá de standard/engineer
- Gestión administrativa de usuarios (CRUD admin)
- Integración PocketBase como auth provider
- MFA / 2FA
- Auditoría de eventos de seguridad (login attempts log)

---

## Assumptions

- Usuarios acceden vía navegador web moderno con localStorage/sessionStorage disponible.
- Un usuario operativo corresponde a una identidad en `app_user`; no hay cuentas compartidas en v1.
- Plan "Free" es suficiente para operaciones MVP; planes Premium existen como atributo display (demo users).
- Engineer role se deriva de convención admin existente hasta spec RBAC futura.
- Warehouse analítico puede estar vacío sin bloquear registro/login (app tables independientes).
- Idiomas ES/EN cubren usuarios operativos iniciales.

---

**Version**: 1.0.0-spec | **Author**: Spec-Driven Development — `/speckit-specify`  
**Next Step**: `/speckit-clarify` (opcional) → `/speckit-checklist` → `/speckit-plan`
