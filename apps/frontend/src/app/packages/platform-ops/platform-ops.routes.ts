import { Routes } from '@angular/router';

export const PLATFORM_OPS_ROUTES: Routes = [
  { path: 'platform-ops', loadComponent: () => import('./pages/platform-ops-dashboard.page').then(m => m.PlatformOpsDashboardPage), title: 'Platform Operations' },
];
