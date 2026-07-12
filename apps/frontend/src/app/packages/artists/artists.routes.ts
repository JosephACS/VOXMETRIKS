import { Routes } from '@angular/router';

/**
 * Routes for the business Artists & Team Management feature (Spec 020).
 *
 * NOTE: mounted under /artist-profiles, not /artists — the /artists and
 * /artists/:id paths are already used by the analytics/streaming
 * music-catalog feature (dim_artista-backed). See app.routes.ts.
 */
export const ARTIST_PROFILES_ROUTES: Routes = [
  {
    path: 'artist-profiles',
    loadComponent: () =>
      import('./pages/artist-profiles-list.page').then((m) => m.ArtistProfilesListPage),
    title: 'Artist Profiles',
  },
  {
    path: 'artist-profiles/:id',
    loadComponent: () =>
      import('./pages/artist-profile-detail.page').then((m) => m.ArtistProfileDetailPage),
    title: 'Artist Profile',
  },
  {
    path: 'artist-profiles/:id/team',
    loadComponent: () =>
      import('./pages/artist-profile-team.page').then((m) => m.ArtistProfileTeamPage),
    title: 'Artist Team',
  },
  {
    path: 'artist-profiles/:id/history',
    loadComponent: () =>
      import('./pages/artist-profile-history.page').then((m) => m.ArtistProfileHistoryPage),
    title: 'Artist History',
  },
];
