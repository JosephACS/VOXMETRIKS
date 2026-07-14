import { Routes } from '@angular/router';

export const BUSINESS_ANALYTICS_ROUTES: Routes = [
  {
    path: 'business-analytics',
    loadComponent: () =>
      import('./pages/biz-analytics-dashboard.page').then((m) => m.BizAnalyticsDashboardPage),
    title: 'Analítica empresarial',
  },
  {
    path: 'business-analytics/kpis',
    loadComponent: () => import('./pages/kpi-explorer.page').then((m) => m.KpiExplorerPage),
    title: 'Explorador KPI',
  },
  {
    path: 'business-analytics/alerts',
    loadComponent: () => import('./pages/biz-alerts.page').then((m) => m.BizAlertsPage),
    title: 'Alertas',
  },
  {
    path: 'business-analytics/recommendations',
    loadComponent: () =>
      import('./pages/biz-recommendations.page').then((m) => m.BizRecommendationsPage),
    title: 'Recomendaciones',
  },
  {
    path: 'business-analytics/quality',
    loadComponent: () => import('./pages/biz-quality.page').then((m) => m.BizQualityPage),
    title: 'Calidad de datos',
  },
];
