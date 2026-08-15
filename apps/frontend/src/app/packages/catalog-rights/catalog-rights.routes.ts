import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

/**
 * Catalog Rights — org operational module (spec 037 FE↔BE alignment).
 * Backend remains authority via Org RBAC + X-Organization-Id.
 */
export const CATALOG_RIGHTS_ROUTES: Routes = [
  {
    path: 'catalog-rights',
    redirectTo: 'catalog-rights/assets',
    pathMatch: 'full',
  },
  {
    path: 'catalog-rights/assets',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'rights.view')],
    loadComponent: () =>
      import('./pages/catalog-assets-list.page').then((m) => m.CatalogAssetsListPage),
    title: 'Activos de catálogo',
  },
  {
    path: 'catalog-rights/assets/:id',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'rights.view')],
    loadComponent: () =>
      import('./pages/catalog-asset-detail.page').then((m) => m.CatalogAssetDetailPage),
    title: 'Activo de catálogo',
  },
  {
    path: 'catalog-rights/releases',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'rights.view')],
    loadComponent: () =>
      import('./pages/catalog-releases-list.page').then((m) => m.CatalogReleasesListPage),
    title: 'Lanzamientos',
  },
  {
    path: 'catalog-rights/contracts',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'rights.view')],
    loadComponent: () =>
      import('./pages/rights-contracts-list.page').then((m) => m.RightsContractsListPage),
    title: 'Contratos de derechos',
  },
  {
    path: 'catalog-rights/contracts/:id',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'rights.view')],
    loadComponent: () =>
      import('./pages/rights-contract-detail.page').then((m) => m.RightsContractDetailPage),
    title: 'Contrato de derechos',
  },
  {
    path: 'catalog-rights/contracts/:id/history',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'rights.view')],
    loadComponent: () =>
      import('./pages/rights-contract-history.page').then((m) => m.RightsContractHistoryPage),
    title: 'Historial de contrato',
  },
  {
    path: 'catalog-rights/conflicts',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational', 'rights.view')],
    loadComponent: () =>
      import('./pages/rights-conflicts-list.page').then((m) => m.RightsConflictsListPage),
    title: 'Conflictos de derechos',
  },
];
