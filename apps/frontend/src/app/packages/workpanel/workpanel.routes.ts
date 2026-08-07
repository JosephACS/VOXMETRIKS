import { Routes } from '@angular/router';
import { staffCapabilityGuard } from '../../core/guards/staff-capability.guard';

export const WORKPANEL_ROUTES: Routes = [
  {
    path: 'workpanel',
    title: 'Workpanel',
    canActivate: [staffCapabilityGuard],
    loadComponent: () =>
      import('./pages/workpanel.page').then((m) => m.WorkpanelPage),
  },
];
