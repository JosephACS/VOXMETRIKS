import { Routes } from '@angular/router';

export const CUSTOMER_SUCCESS_ROUTES: Routes = [
  {
    path: 'customer-success',
    loadComponent: () =>
      import('./pages/cs-dashboard.page').then((m) => m.CsDashboardPage),
    title: 'Customer Success',
  },
  {
    path: 'support',
    loadComponent: () =>
      import('./pages/support-list.page').then((m) => m.SupportListPage),
    title: 'Support',
  },
  {
    path: 'support/:id',
    loadComponent: () =>
      import('./pages/support-detail.page').then((m) => m.SupportDetailPage),
    title: 'Support Case',
  },
];
