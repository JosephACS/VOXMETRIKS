import { Routes } from '@angular/router';

export const ROYALTIES_ROUTES: Routes = [
  {
    path: 'royalties',
    loadComponent: () =>
      import('./pages/royalties-dashboard.page').then((m) => m.RoyaltiesDashboardPage),
    title: 'Regalías',
  },
  {
    path: 'royalties/pools',
    loadComponent: () =>
      import('./pages/pools-list.page').then((m) => m.PoolsListPage),
    title: 'Fondos de regalías',
  },
  {
    path: 'royalties/pools/:id',
    loadComponent: () =>
      import('./pages/pool-detail.page').then((m) => m.PoolDetailPage),
    title: 'Detalle del fondo',
  },
  {
    path: 'royalties/settlements',
    loadComponent: () =>
      import('./pages/settlements-list.page').then((m) => m.SettlementsListPage),
    title: 'Liquidaciones',
  },
  {
    path: 'royalties/settlements/:id',
    loadComponent: () =>
      import('./pages/settlement-detail.page').then((m) => m.SettlementDetailPage),
    title: 'Detalle de liquidación',
  },
  {
    path: 'royalties/statements',
    loadComponent: () =>
      import('./pages/statements-list.page').then((m) => m.StatementsListPage),
    title: 'Estados de cuenta',
  },
  {
    path: 'payouts',
    loadComponent: () =>
      import('./pages/payouts-list.page').then((m) => m.PayoutsListPage),
    title: 'Pagos simulados',
  },
  {
    path: 'payouts/:id',
    loadComponent: () =>
      import('./pages/payout-detail.page').then((m) => m.PayoutDetailPage),
    title: 'Detalle de pago simulado',
  },
];
