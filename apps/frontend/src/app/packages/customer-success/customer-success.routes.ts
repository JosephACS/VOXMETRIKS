import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

export const CUSTOMER_SUCCESS_ROUTES: Routes = [
  {
    path: 'customer-success',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'customer_success.view'),
    ],
    loadComponent: () =>
      import('./pages/cs-dashboard.page').then((m) => m.CsDashboardPage),
    title: 'Éxito del cliente',
  },
  {
    path: 'support',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'support.view'),
    ],
    loadComponent: () =>
      import('./pages/support-list.page').then((m) => m.SupportListPage),
    title: 'Soporte',
  },
  {
    path: 'support/:id',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'support.view'),
    ],
    loadComponent: () =>
      import('./pages/support-detail.page').then((m) => m.SupportDetailPage),
    title: 'Caso de soporte',
  },
];
