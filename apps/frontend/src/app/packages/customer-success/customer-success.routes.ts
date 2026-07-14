import { Routes } from '@angular/router';

export const CUSTOMER_SUCCESS_ROUTES: Routes = [
  {
    path: 'customer-success',
    loadComponent: () =>
      import('./pages/cs-dashboard.page').then((m) => m.CsDashboardPage),
    title: 'Éxito del cliente',
  },
  {
    path: 'support',
    loadComponent: () =>
      import('./pages/support-list.page').then((m) => m.SupportListPage),
    title: 'Soporte',
  },
  {
    path: 'support/:id',
    loadComponent: () =>
      import('./pages/support-detail.page').then((m) => m.SupportDetailPage),
    title: 'Caso de soporte',
  },
];
