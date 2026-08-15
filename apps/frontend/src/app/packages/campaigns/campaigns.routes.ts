import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

export const CAMPAIGNS_ROUTES: Routes = [
  {
    path: 'campaigns',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'campaign.view'),
    ],
    loadComponent: () => import('./pages/campaigns-list.page').then((m) => m.CampaignsListPage),
    title: 'Campañas',
  },
  {
    path: 'campaigns/:id',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'campaign.view'),
    ],
    loadComponent: () => import('./pages/campaign-detail.page').then((m) => m.CampaignDetailPage),
    title: 'Detalle de campaña',
  },
];
