import { Routes } from '@angular/router';

export const BUSINESS_ANALYTICS_ROUTES: Routes = [
  { path: 'business-analytics', loadComponent: () => import('./pages/biz-analytics-dashboard.page').then(m => m.BizAnalyticsDashboardPage), title: 'Business Analytics' },
  { path: 'business-analytics/kpis', loadComponent: () => import('./pages/kpi-explorer.page').then(m => m.KpiExplorerPage), title: 'KPI Explorer' },
  { path: 'business-analytics/alerts', loadComponent: () => import('./pages/biz-alerts.page').then(m => m.BizAlertsPage), title: 'Alerts' },
  { path: 'business-analytics/recommendations', loadComponent: () => import('./pages/biz-recommendations.page').then(m => m.BizRecommendationsPage), title: 'Recommendations' },
  { path: 'business-analytics/quality', loadComponent: () => import('./pages/biz-quality.page').then(m => m.BizQualityPage), title: 'Data Quality' },
];
