import { Routes } from '@angular/router';

/**
 * Routes for the Catalog Rights & Contracts feature (Spec 021).
 *
 * Mounted under /catalog-rights/*. This feature tracks catalog ownership
 * and licensing rights (`app_rights_contract`), which is distinct from
 * the CRM's commercial sales contracts (`app_commercial_contract`).
 */
export const CATALOG_RIGHTS_ROUTES: Routes = [
  {
    path: 'catalog-rights',
    redirectTo: 'catalog-rights/assets',
    pathMatch: 'full',
  },
  {
    path: 'catalog-rights/assets',
    loadComponent: () =>
      import('./pages/catalog-assets-list.page').then((m) => m.CatalogAssetsListPage),
    title: 'Catalog Assets',
  },
  {
    path: 'catalog-rights/assets/:id',
    loadComponent: () =>
      import('./pages/catalog-asset-detail.page').then((m) => m.CatalogAssetDetailPage),
    title: 'Catalog Asset',
  },
  {
    path: 'catalog-rights/releases',
    loadComponent: () =>
      import('./pages/catalog-releases-list.page').then((m) => m.CatalogReleasesListPage),
    title: 'Catalog Releases',
  },
  {
    path: 'catalog-rights/contracts',
    loadComponent: () =>
      import('./pages/rights-contracts-list.page').then((m) => m.RightsContractsListPage),
    title: 'Rights Contracts',
  },
  {
    path: 'catalog-rights/contracts/:id',
    loadComponent: () =>
      import('./pages/rights-contract-detail.page').then((m) => m.RightsContractDetailPage),
    title: 'Rights Contract',
  },
  {
    path: 'catalog-rights/contracts/:id/history',
    loadComponent: () =>
      import('./pages/rights-contract-history.page').then((m) => m.RightsContractHistoryPage),
    title: 'Contract History',
  },
  {
    path: 'catalog-rights/conflicts',
    loadComponent: () =>
      import('./pages/rights-conflicts-list.page').then((m) => m.RightsConflictsListPage),
    title: 'Rights Conflicts',
  },
];
