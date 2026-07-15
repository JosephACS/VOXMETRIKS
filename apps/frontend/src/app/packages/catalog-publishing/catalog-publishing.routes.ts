import { Routes } from '@angular/router';

export const CATALOG_PUBLISHING_ROUTES: Routes = [
  {
    path: 'artist',
    redirectTo: 'artist/releases',
    pathMatch: 'full',
  },
  {
    path: 'artist/profile',
    loadComponent: () =>
      import('./pages/artist-profile.page').then((m) => m.ArtistProfilePage),
    title: 'publishing.profile.title',
  },
  {
    path: 'artist/releases/new',
    loadComponent: () =>
      import('./pages/artist-release-wizard.page').then((m) => m.ArtistReleaseWizardPage),
    title: 'publishing.wizard.title',
  },
  {
    path: 'artist/releases/:id',
    loadComponent: () =>
      import('./pages/artist-release-detail.page').then((m) => m.ArtistReleaseDetailPage),
    title: 'publishing.detail.title',
  },
  {
    path: 'artist/releases',
    loadComponent: () =>
      import('./pages/artist-releases-list.page').then((m) => m.ArtistReleasesListPage),
    title: 'publishing.releases.title',
  },
  {
    path: 'artist/tracks',
    loadComponent: () =>
      import('./pages/artist-tracks-list.page').then((m) => m.ArtistTracksListPage),
    title: 'publishing.tracks.title',
  },
  {
    path: 'catalog-review/:id',
    loadComponent: () =>
      import('./pages/catalog-review-detail.page').then((m) => m.CatalogReviewDetailPage),
    title: 'publishing.review.detailTitle',
  },
  {
    path: 'catalog-review',
    loadComponent: () =>
      import('./pages/catalog-review-inbox.page').then((m) => m.CatalogReviewInboxPage),
    title: 'publishing.review.inboxTitle',
  },
];
