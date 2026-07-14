import { Routes } from '@angular/router';

export const PERSONAL_ACCOUNT_ROUTES: Routes = [
  {
    path: 'account/plans',
    title: 'personal.plans.title',
    loadComponent: () =>
      import('./pages/personal-plans.page').then((m) => m.PersonalPlansPage),
  },
  {
    path: 'account/subscription',
    title: 'personal.subscription.title',
    loadComponent: () =>
      import('./pages/personal-subscription.page').then((m) => m.PersonalSubscriptionPage),
  },
  {
    path: 'account/household',
    title: 'personal.household.title',
    loadComponent: () =>
      import('./pages/personal-household.page').then((m) => m.PersonalHouseholdPage),
  },
  {
    path: 'account/billing',
    title: 'personal.billing.title',
    loadComponent: () =>
      import('./pages/personal-billing.page').then((m) => m.PersonalBillingPage),
  },
];
