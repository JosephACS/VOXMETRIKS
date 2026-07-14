import { Routes } from '@angular/router';

export const REPORTING_ROUTES: Routes = [
  {
    path: 'reports',
    loadComponent: () => import('./pages/reports-list.page').then((m) => m.ReportsListPage),
    title: 'Reportes ejecutivos',
  },
  {
    path: 'reports/:id',
    loadComponent: () => import('./pages/report-detail.page').then((m) => m.ReportDetailPage),
    title: 'Detalle de reporte',
  },
  {
    path: 'business-decisions',
    loadComponent: () => import('./pages/decisions-list.page').then((m) => m.DecisionsListPage),
    title: 'Decisiones empresariales',
  },
  {
    path: 'business-decisions/:id',
    loadComponent: () => import('./pages/decision-detail.page').then((m) => m.DecisionDetailPage),
    title: 'Detalle de decisión',
  },
];
