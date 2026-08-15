import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

export const BUSINESS_ANALYTICS_ROUTES: Routes = [
  {
    path: 'business-analytics',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'biz_analytics.view'),
    ],
    loadComponent: () =>
      import('./pages/biz-analytics-dashboard.page').then((m) => m.BizAnalyticsDashboardPage),
    title: 'Dirección estratégica',
  },
  {
    path: 'business-analytics/kpis',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'biz_analytics.view'),
    ],
    loadComponent: () => import('./pages/kpi-explorer.page').then((m) => m.KpiExplorerPage),
    title: 'Explorador KPI',
  },
  {
    path: 'business-analytics/alerts',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'biz_analytics.view'),
    ],
    loadComponent: () => import('./pages/biz-alerts.page').then((m) => m.BizAlertsPage),
    title: 'Alertas',
  },
  {
    path: 'business-analytics/recommendations',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'biz_analytics.view'),
    ],
    loadComponent: () =>
      import('./pages/biz-recommendations.page').then((m) => m.BizRecommendationsPage),
    title: 'Recomendaciones',
  },
  {
    path: 'business-analytics/quality',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'biz_analytics.view'),
    ],
    loadComponent: () => import('./pages/biz-quality.page').then((m) => m.BizQualityPage),
    title: 'Calidad de datos',
  },
];
