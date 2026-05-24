# VOXMETRIK_V2 — PASO 5: Layouts

## ✅ Contenido del ZIP

Este ZIP contiene los dos layouts principales de la aplicación:

### Estructura
```
src/
└── app/
    └── layouts/
        ├── auth-layout/
        │   ├── auth-layout.component.ts
        │   ├── auth-layout.component.html
        │   └── auth-layout.component.css
        └── dashboard-layout/
            ├── dashboard-layout.component.ts
            ├── dashboard-layout.component.html
            └── dashboard-layout.component.css
```

## 📋 Instrucciones de instalación

### Rápida
1. Descomprime el ZIP
2. Copia la carpeta `src/app/layouts/` en tu proyecto `frontend/app/src/app/`
3. **NOTA:** Si ya existe `src/app/layouts/`, REEMPLAZA todo

### Verificar estructura final
Después de copiar:
```
src/app/layouts/
├── auth-layout/
│   ├── auth-layout.component.ts
│   ├── auth-layout.component.html
│   └── auth-layout.component.css
└── dashboard-layout/
    ├── dashboard-layout.component.ts
    ├── dashboard-layout.component.html
    └── dashboard-layout.component.css
```

## 📖 Descripción de layouts

---

### 1. **Auth Layout** (`auth-layout/`)

**Propósito:** Layout minimalista para páginas de autenticación (login, register, etc.)

**Características:**
- ✅ Página centrada (max-width: 400px)
- ✅ Fondo oscuro con gradiente y grid sutil
- ✅ Branding VOXMETRIK (logo + texto animado)
- ✅ Footer con año y créditos
- ✅ Responsive en móvil
- ✅ Sin sidebar ni topbar

**Estructura visual:**
```
┌─────────────────────────────────┐
│                                 │
│        [Background grid]        │
│                                 │
│        ┌────────────────┐       │
│        │      ♪         │       │
│        │   VOXMETRIK    │       │
│        ├────────────────┤       │
│        │  [Form aquí]   │       │
│        │  (login page)  │       │
│        ├────────────────┤       │
│        │ Music Platform │       │
│        └────────────────┘       │
│                                 │
└─────────────────────────────────┘
```

**Uso en rutas:**
```typescript
// En app.routes.ts (ya configurado en PASO 1)
{
  path: 'login',
  canActivate: [publicGuard],
  loadComponent: () =>
    import('./pages/login/login.component').then(
      (m) => m.LoginComponent
    ),
}
```

**Estilos destacados:**
- Animación float del ícono
- Gradiente en el texto VOXMETRIK
- Grid sutil de fondo
- Responsive a 768px y 480px

---

### 2. **Dashboard Layout** (`dashboard-layout/`)

**Propósito:** Layout principal para el dashboard con sidebar, topbar y área de contenido

**Características:**
- ✅ Topbar sticky con logo, usuario y logout
- ✅ Sidebar colapsible con navegación
- ✅ Área principal de contenido (router-outlet)
- ✅ Loading spinner global (fullpage)
- ✅ Responsive: sidebar se convierte en menú mobile
- ✅ Avatar del usuario con inicial
- ✅ Botón logout con redirección

**Estructura visual:**
```
┌──────────────────────────────────────┐
│  ♪ VOXMETRIK  |  [👤 User] [🚪]    │ ← Topbar
├────┬──────────────────────────────────┤
│    │                                  │
│ 📊 │  [Contenido dinámico]           │
│ 👥 │  router-outlet                  │
│ 🎵 │                                  │
│ 🎸 │                                  │
│    │  Loading spinner (si hay        │
│    │  requests HTTP)                 │
└────┴──────────────────────────────────┘
  ↑
Sidebar
```

**Componentes integrados:**
- Logo clickeable
- Avatar con inicial del usuario
- Nombre de usuario (truncado si es muy largo)
- Rol: "Music Intelligence"
- Navegación: Overview, Artists, Tracks, Genres
- Loading spinner global del PASO 3

**Métodos públicos:**
```typescript
toggleSidebar(): void           // Toggle sidebar en móvil
logout(): void                  // Logout y redirigir a /login
closeSidebarOnNav(): void       // Cerrar sidebar al navegar
```

**Propiedades reactivas (signals):**
```typescript
protected sidebarCollapsed = signal(false);  // Estado del sidebar
protected userName = signal('User');        // Nombre del usuario
protected navItems = [...]                  // Items de navegación
```

**Inyecciones:**
```typescript
private readonly authService = inject(AuthService);
protected readonly loadingService = inject(LoadingService);
private readonly router = inject(Router);
```

---

## ⚠️ IMPORTANTE

### Rutas y Guards

Ambos layouts están ya registrados en `app.routes.ts` (PASO 1):

**Auth Layout** — Acceso público (protegido con `publicGuard`):
```typescript
{
  path: 'login',
  canActivate: [publicGuard],
  loadComponent: () => AuthLayoutComponent,
  children: [...]
}
```

**Dashboard Layout** — Acceso protegido (protegido con `authGuard`):
```typescript
{
  path: 'dashboard',
  canActivate: [authGuard],
  loadComponent: () => DashboardLayoutComponent,
  children: [
    { path: 'overview', ... },
    { path: 'artists', ... },
    { path: 'tracks', ... },
    { path: 'genres', ... },
  ]
}
```

### Responsive design

Ambos layouts son **100% responsive**:

| Viewport | Auth Layout | Dashboard Layout |
|----------|-------------|------------------|
| Desktop (>768px) | 400px centered | Sidebar visible + content |
| Tablet (768px) | Full width | Sidebar colapsable |
| Mobile (<480px) | Full width | Sidebar hidden (menu toggle) |

---

## 🎨 Personalización

### Cambiar colores

Los estilos heredan de `src/styles.css`:
- `--color-primary` (verde)
- `--color-surface` (fondo superficie)
- `--color-text` (texto principal)

Modifica `src/styles.css` para cambiar tema globalmente.

### Cambiar íconos

En `dashboard-layout.component.ts`:
```typescript
protected readonly navItems = [
  { label: 'Overview', path: '/dashboard/overview', icon: '📊' }, // Cambiar emoji
  // ...
];
```

O en `auth-layout.component.html`:
```html
<div class="brand-icon">♪</div> <!-- Cambiar ícono -->
```

### Cambiar velocidad de animaciones

En `dashboard-layout.component.css`:
```css
.btn-menu-toggle span {
  transition: all var(--transition);  /* Heredado de styles.css */
}
```

Modifica `--transition` en `src/styles.css` para cambiar globalmente.

---

## 🔌 Integración con servicios

### Loading spinner global

El `LoadingService` (PASO 1) inyecta automáticamente:

```typescript
protected readonly loadingService = inject(LoadingService);
```

Cualquier request HTTP activa el spinner fullpage:
```html
@if (loadingService.isLoading()) {
  <app-loading-spinner [fullpage]="true" label="Loading..." />
}
```

### Logout automático

Si el API retorna 401, el `apiInterceptor` (PASO 1) llama automáticamente:
```typescript
authService.logout();
router.navigate(['/login']);
```

---

## ✅ Verificación post-instalación

```bash
cd frontend/app

# Compilar
ng build

# Servir en desarrollo
ng serve
```

Debe compilar sin errores.

**Prueba visual (cuando PASO 6+ esté listo):**
1. Abre `http://localhost:4200`
2. Deberías ver login page (Auth Layout)
3. Haz login (cualquier credencial, es mock)
4. Deberías ver dashboard (Dashboard Layout) con:
   - Topbar con logo, usuario, logout
   - Sidebar con navegación
   - Área principal vacía (esperando componentes en PASO 6+)

---

## 📖 Siguiente paso

Una vez verificado, espera instrucciones para el **PASO 6: Login Page**

---

**Fecha generado:** PASO 5
**Versión Angular:** 21+ (Standalone Components)
**CSS:** Design tokens globales de `src/styles.css`
**Guards:** authGuard, publicGuard (PASO 1)
