import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

/** Catalog publishing / artist portal — org operational (spec 037). */
export const CATALOG_PUBLISHING_ROUTES: Routes = [
  {
    path: 'catalog',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational')],
    loadComponent: () =>
      import('./pages/catalog-hub.page').then((m) => m.CatalogHubPage),
    title: 'Catálogo y publicación',
  },
  {
    path: 'artist',
    redirectTo: 'artist/releases',
    pathMatch: 'full',
  },
  {
    path: 'artist/profile',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'artist.view'),
    ],
    loadComponent: () =>
      import('./pages/artist-profile.page').then((m) => m.ArtistProfilePage),
    title: 'publishing.profile.title',
  },
  {
    path: 'artist/releases/new',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'publishing.create'),
    ],
    data: { releaseContext: 'organization' },
    loadComponent: () =>
      import('./pages/artist-release-wizard.page').then((m) => m.ArtistReleaseWizardPage),
    title: 'publishing.wizard.title',
  },
  {
    path: 'artist/releases/:id',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'publishing.view'),
    ],
    loadComponent: () =>
      import('./pages/artist-release-detail.page').then((m) => m.ArtistReleaseDetailPage),
    title: 'publishing.detail.title',
  },
  {
    path: 'artist/releases',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'publishing.view'),
    ],
    loadComponent: () =>
      import('./pages/artist-releases-list.page').then((m) => m.ArtistReleasesListPage),
    title: 'publishing.releases.title',
  },
  {
    path: 'artist/tracks',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'publishing.view'),
    ],
    loadComponent: () =>
      import('./pages/artist-tracks-list.page').then((m) => m.ArtistTracksListPage),
    title: 'publishing.tracks.title',
  },
  {
    path: 'catalog-review/:id',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'publishing.review'),
    ],
    loadComponent: () =>
      import('./pages/catalog-review-detail.page').then((m) => m.CatalogReviewDetailPage),
    title: 'publishing.review.detailTitle',
  },
  {
    path: 'catalog-review',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'publishing.review'),
    ],
    loadComponent: () =>
      import('./pages/catalog-review-inbox.page').then((m) => m.CatalogReviewInboxPage),
    title: 'publishing.review.inboxTitle',
  },
];
