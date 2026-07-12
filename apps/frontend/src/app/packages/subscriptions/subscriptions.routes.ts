import { Routes } from '@angular/router';

export const SUBSCRIPTIONS_ROUTES: Routes = [
  {
    path: 'subscriptions',
    redirectTo: 'subscriptions/overview',
    pathMatch: 'full',
  },
  {
    path: 'subscriptions/plans',
    title: 'Planes — Voxmetrik',
    loadComponent: () =>
      import('./pages/plans-catalog.page').then((m) => m.PlansCatalogPageComponent),
  },
  {
    path: 'subscriptions/plans/:id',
    title: 'Plan — Voxmetrik',
    loadComponent: () =>
      import('./pages/plan-detail.page').then((m) => m.PlanDetailPageComponent),
  },
  {
    path: 'subscriptions/overview',
    title: 'Mi Suscripción — Voxmetrik',
    loadComponent: () =>
      import('./pages/subscription-overview.page').then((m) => m.SubscriptionOverviewPageComponent),
  },
  {
    path: 'subscriptions/trial',
    title: 'Iniciar Trial — Voxmetrik',
    loadComponent: () =>
      import('./pages/trial-start.page').then((m) => m.TrialStartPageComponent),
  },
  {
    path: 'subscriptions/:id/cancel',
    title: 'Cancelar Suscripción — Voxmetrik',
    loadComponent: () =>
      import('./pages/subscription-cancel.page').then((m) => m.SubscriptionCancelPageComponent),
  },
  {
    path: 'subscriptions/:id/addons',
    title: 'Addons — Voxmetrik',
    loadComponent: () =>
      import('./pages/subscription-addons.page').then((m) => m.SubscriptionAddonsPageComponent),
  },
  {
    path: 'subscriptions/:id/usage',
    title: 'Uso — Voxmetrik',
    loadComponent: () =>
      import('./pages/subscription-usage.page').then((m) => m.SubscriptionUsagePageComponent),
  },
];
