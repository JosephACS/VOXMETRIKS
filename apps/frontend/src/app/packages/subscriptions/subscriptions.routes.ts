import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

export const SUBSCRIPTIONS_ROUTES: Routes = [
  {
    path: 'subscriptions',
    redirectTo: 'subscriptions/overview',
    pathMatch: 'full',
  },
  {
    path: 'subscriptions/plans',
    title: 'Planes',
    // Authenticated users may browse the catalog before creating an org.
    loadComponent: () =>
      import('./pages/plans-catalog.page').then((m) => m.PlansCatalogPageComponent),
  },
  {
    path: 'subscriptions/plans/:id',
    title: 'Plan',
    loadComponent: () =>
      import('./pages/plan-detail.page').then((m) => m.PlanDetailPageComponent),
  },
  {
    path: 'subscriptions/overview',
    title: 'Mi suscripción',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('onboarding', 'subscription.view')],
    loadComponent: () =>
      import('./pages/subscription-overview.page').then((m) => m.SubscriptionOverviewPageComponent),
  },
  {
    path: 'subscriptions/trial',
    title: 'Iniciar prueba',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('onboarding', 'subscription.create')],
    loadComponent: () =>
      import('./pages/trial-start.page').then((m) => m.TrialStartPageComponent),
  },
  {
    path: 'subscriptions/select-plan',
    title: 'Seleccionar plan',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('onboarding', 'subscription.create')],
    loadComponent: () =>
      import('./pages/subscription-select-plan.page').then((m) => m.SubscriptionSelectPlanPage),
  },
  {
    path: 'subscriptions/checkout',
    title: 'checkout.title',
    data: { checkoutScope: 'organization' },
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('onboarding', 'subscription.create'),
    ],
    loadComponent: () =>
      import('../checkout/pages/checkout-journey.page').then((m) => m.CheckoutJourneyPage),
  },
  {
    path: 'subscriptions/:id/cancel',
    title: 'Cancelar suscripción',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'subscription.change')],
    loadComponent: () =>
      import('./pages/subscription-cancel.page').then((m) => m.SubscriptionCancelPageComponent),
  },
  {
    path: 'subscriptions/:id/addons',
    title: 'Complementos',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'subscription.change')],
    loadComponent: () =>
      import('./pages/subscription-addons.page').then((m) => m.SubscriptionAddonsPageComponent),
  },
  {
    path: 'subscriptions/:id/usage',
    title: 'Uso',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'subscription.view')],
    loadComponent: () =>
      import('./pages/subscription-usage.page').then((m) => m.SubscriptionUsagePageComponent),
  },
];
