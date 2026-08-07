import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

export const ROYALTIES_ROUTES: Routes = [
  {
    path: 'royalties',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/royalties-dashboard.page').then((m) => m.RoyaltiesDashboardPage),
    title: 'Regalías',
  },
  {
    path: 'royalties/pools',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/pools-list.page').then((m) => m.PoolsListPage),
    title: 'Fondos de regalías',
  },
  {
    path: 'royalties/pools/:id',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/pool-detail.page').then((m) => m.PoolDetailPage),
    title: 'Detalle del fondo',
  },
  {
    path: 'royalties/settlements',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/settlements-list.page').then((m) => m.SettlementsListPage),
    title: 'Liquidaciones',
  },
  {
    path: 'royalties/settlements/:id',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/settlement-detail.page').then((m) => m.SettlementDetailPage),
    title: 'Detalle de liquidación',
  },
  {
    path: 'royalties/statements',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/statements-list.page').then((m) => m.StatementsListPage),
    title: 'Estados de cuenta',
  },
  {
    path: 'payouts',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/payouts-list.page').then((m) => m.PayoutsListPage),
    title: 'Pagos de regalías',
  },
  {
    path: 'payouts/:id',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'royalty.view')],
    loadComponent: () =>
      import('./pages/payout-detail.page').then((m) => m.PayoutDetailPage),
    title: 'Detalle de pago',
  },
];
