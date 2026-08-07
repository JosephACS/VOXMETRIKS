import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

/**
 * Routes for the business Artists & Team Management feature (Spec 020).
 *
 * NOTE: mounted under /artist-profiles, not /artists — the /artists and
 * /artists/:id paths are already used by the analytics/streaming
 * music-catalog feature (dim_artista-backed). See app.routes.ts.
 *
 * Spec 043 hotfix: require org context before paint (F5 / deep link).
 */
export const ARTIST_PROFILES_ROUTES: Routes = [
  {
    path: 'artist-profiles',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational')],
    loadComponent: () =>
      import('./pages/artist-profiles-list.page').then((m) => m.ArtistProfilesListPage),
    title: 'Perfiles de artista',
  },
  {
    path: 'artist-profiles/:id',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational')],
    loadComponent: () =>
      import('./pages/artist-profile-detail.page').then((m) => m.ArtistProfileDetailPage),
    title: 'Perfil de artista',
  },
  {
    path: 'artist-profiles/:id/team',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational')],
    loadComponent: () =>
      import('./pages/artist-profile-team.page').then((m) => m.ArtistProfileTeamPage),
    title: 'Equipo del artista',
  },
  {
    path: 'artist-profiles/:id/history',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('operational')],
    loadComponent: () =>
      import('./pages/artist-profile-history.page').then((m) => m.ArtistProfileHistoryPage),
    title: 'Historial del artista',
  },
];
