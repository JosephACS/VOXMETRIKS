# Frontend — Angular SPA

## Stack

| Tecnología | Versión | Uso |
|------------|---------|-----|
| Angular | 21 | Framework SPA |
| RxJS | 7.x | Streams reactivos |
| Angular Material | — | UI components |
| ECharts | — | Gráficos dashboard enterprise |
| Standalone components | — | Sin NgModules |

## Métricas

| Métrica | Valor |
|---------|------:|
| Componentes Angular | 46 |
| Servicios injectables | 24 (+ 4 API clients) |
| Rutas lazy-loaded | 27 |
| Archivos TS en `app/` | 114 |

## Estructura

```
frontend/src/app/
├── app.routes.ts           # Definición de rutas
├── app.config.ts           # Providers globales
├── core/                   # Auth, guards, interceptors, i18n
│   ├── services/           # ApiService, DashboardService, AuthService
│   ├── guards/             # authGuard, engineerGuard
│   └── interceptors/       # loading, auth-error, api
├── features/               # Analytics Hub enterprise (nuevo)
│   ├── dashboard/
│   ├── analytics/
│   ├── tracks/
│   └── users/
├── packages/               # Dominios legacy
│   ├── streaming/          # Discover, catálogo, player
│   ├── analytics/          # Trending, comparatives
│   ├── data-engineering/   # ELT pipeline, explorer
│   ├── users/
│   └── recommendations/
├── shared/                 # Componentes reutilizables
│   ├── components/         # player-bar, empty-state, chart-widget
│   └── services/           # MusicPlayerService, LoadingService
└── layouts/                # auth-layout, dashboard-layout
```

## Rutas principales

| Ruta | Componente | Descripción |
|------|------------|-------------|
| `/login` | LoginComponent | Autenticación |
| `/dashboard` | features/dashboard | Analytics Hub enterprise |
| `/discover` | packages/home | Home streaming |
| `/insights/analytics` | features/analytics | Analytics enterprise |
| `/insights/tracks` | features/tracks | Top tracks |
| `/insights/users` | features/users | User insights |
| `/tracks` | packages/tracks | Catálogo completo |
| `/analytics` | packages/analytics | Analytics legacy |
| `/recommendations` | packages/recommendations | UI recomendaciones |
| `/elt-pipeline` | EltPipelineComponent | Engineer only |
| `/explorer` | ExplorerComponent | Engineer only |

## Lazy loading

Todas las páginas usan `loadComponent()` con dynamic `import()`. Layouts (`AuthLayout`, `DashboardLayout`) y `App` root son eager.

## Servicios core (enterprise)

| Servicio | Endpoint backend |
|----------|------------------|
| `DashboardService` | `/api/v1/dashboard/overview`, `/api/v1/analytics/streams` |
| `EnterpriseTracksService` | `/api/v1/tracks/top`, recommendations |
| `UsersService` | `/api/v1/users/{id}/insights` |
| `ApiService` | Wrapper HTTP genérico |

## Interceptors

| Interceptor | Función |
|-------------|---------|
| `api.interceptor` | Base URL, headers |
| `auth-error.interceptor` | Redirect en 401 |
| `loading.interceptor` | Spinner global |
| `catalog-steward.interceptor` | Metadata catálogo |

## UX patterns

- **Loading:** `LoadingService` + signals en dashboard enterprise
- **Error / Empty / Retry:** `EmptyStateComponent` con tipos `loading`, `error`, `no-data`
- **Change detection:** `OnPush` en componentes shared
- **Memory:** `takeUntilDestroyed()` en suscripciones

## Ejecución

```bash
cd apps/frontend
npm install
npm start          # http://localhost:4200
npm run build      # producción → dist/
```

## Build producción

```bash
ng build --configuration production
```

Output: `frontend/dist/frontend/browser/`

Ver [deployment.md](../09-deployment/deployment.md) para nginx/Docker.
