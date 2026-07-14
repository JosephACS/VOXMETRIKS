import { Routes } from '@angular/router';

export const CAMPAIGNS_ROUTES: Routes = [
  {
    path: 'campaigns',
    loadComponent: () => import('./pages/campaigns-list.page').then((m) => m.CampaignsListPage),
    title: 'Campañas',
  },
  {
    path: 'campaigns/:id',
    loadComponent: () => import('./pages/campaign-detail.page').then((m) => m.CampaignDetailPage),
    title: 'Detalle de campaña',
  },
];
