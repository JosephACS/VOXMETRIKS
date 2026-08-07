import { Routes } from '@angular/router';
import { staffCapabilityGuard } from '../../core/guards/staff-capability.guard';

export const REPORTING_ROUTES: Routes = [
  {
    path: 'reports',
    canActivate: [staffCapabilityGuard],
    loadComponent: () => import('./pages/reports-hub.page').then((m) => m.ReportsHubPage),
    title: 'Reportes',
  },
  {
    // Legacy executive report detail (demo) — keep deep link, not primary product nav.
    path: 'reports/legacy/:id',
    canActivate: [staffCapabilityGuard],
    loadComponent: () => import('./pages/report-detail.page').then((m) => m.ReportDetailPage),
    title: 'Detalle de reporte',
  },
  {
    path: 'reports/:id',
    redirectTo: '/reports',
    pathMatch: 'full',
  },
  {
    path: 'business-decisions',
    canActivate: [staffCapabilityGuard],
    loadComponent: () => import('./pages/decisions-list.page').then((m) => m.DecisionsListPage),
    title: 'Decisiones empresariales',
  },
  {
    path: 'business-decisions/:id',
    canActivate: [staffCapabilityGuard],
    loadComponent: () => import('./pages/decision-detail.page').then((m) => m.DecisionDetailPage),
    title: 'Detalle de decisión',
  },
];
