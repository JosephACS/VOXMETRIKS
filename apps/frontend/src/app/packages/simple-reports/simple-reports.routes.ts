import { Routes } from '@angular/router';
import { staffCapabilityGuard } from '../../core/guards/staff-capability.guard';

export const SIMPLE_REPORTS_ROUTES: Routes = [
  {
    path: 'simple-reports',
    canActivate: [staffCapabilityGuard],
    loadComponent: () =>
      import('./pages/simple-reports.page').then((m) => m.SimpleReportsPage),
    title: 'Reportes simples',
  },
];
