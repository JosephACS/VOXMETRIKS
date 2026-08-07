import { Routes } from '@angular/router';
import { platformAdminGuard } from '../../core/guards/platform-admin.guard';

export const PLATFORM_OPS_ROUTES: Routes = [
  {
    path: 'platform-ops',
    canActivate: [platformAdminGuard],
    loadComponent: () =>
      import('./pages/platform-ops-dashboard.page').then((m) => m.PlatformOpsDashboardPage),
    title: 'Operaciones de plataforma',
  },
  {
    path: 'platform-ops/audio-unresolved',
    canActivate: [platformAdminGuard],
    loadComponent: () =>
      import('./pages/unresolved-audio.page').then((m) => m.UnresolvedAudioPage),
    title: 'Audio no resuelto',
  },
];
