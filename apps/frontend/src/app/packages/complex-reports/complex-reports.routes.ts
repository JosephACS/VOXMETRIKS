import { Routes } from '@angular/router';
import { staffCapabilityGuard } from '../../core/guards/staff-capability.guard';

export const COMPLEX_REPORTS_ROUTES: Routes = [
  {
    path: 'complex-reports',
    title: 'Informes complejos',
    canActivate: [staffCapabilityGuard],
    loadComponent: () =>
      import('./pages/complex-reports.page').then((m) => m.ComplexReportsPage),
  },
];
