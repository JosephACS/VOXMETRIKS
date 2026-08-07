import { Routes } from '@angular/router';
import { authGuard } from '../../core/guards/auth.guard';
import { platformAdminGuard } from '../../core/guards/platform-admin.guard';
import {
  artistPermissionGuard,
  artistRequiredGuard,
} from './guards/artist-space.guards';

export const ARTIST_SPACE_ROUTES: Routes = [
  {
    path: 'artist-space',
    canActivate: [authGuard, artistRequiredGuard],
    loadComponent: () =>
      import('./pages/artist-space-summary.page').then((m) => m.ArtistSpaceSummaryPage),
    title: 'artistSpace.summary.title',
  },
  {
    path: 'artist-space/summary',
    canActivate: [authGuard, artistRequiredGuard],
    loadComponent: () =>
      import('./pages/artist-space-summary.page').then((m) => m.ArtistSpaceSummaryPage),
    title: 'artistSpace.summary.title',
  },
  {
    path: 'artist-space/profile',
    canActivate: [authGuard, artistRequiredGuard],
    loadComponent: () =>
      import('./pages/artist-space-profile.page').then((m) => m.ArtistSpaceProfilePage),
    title: 'artistSpace.profile.title',
  },
  {
    path: 'artist-space/tracks',
    canActivate: [authGuard, artistRequiredGuard],
    loadComponent: () =>
      import('./pages/artist-space-tracks.page').then((m) => m.ArtistSpaceTracksPage),
    title: 'artistSpace.tracks.title',
  },
  {
    path: 'artist-space/releases',
    canActivate: [authGuard, artistRequiredGuard],
    loadComponent: () =>
      import('./pages/artist-space-releases.page').then((m) => m.ArtistSpaceReleasesPage),
    title: 'artistSpace.releases.title',
  },
  {
    path: 'artist-space/team',
    canActivate: [
      authGuard,
      artistRequiredGuard,
      artistPermissionGuard('artist_space.view'),
    ],
    loadComponent: () =>
      import('./pages/artist-space-team.page').then((m) => m.ArtistSpaceTeamPage),
    title: 'artistSpace.team.title',
  },
  {
    path: 'artist-space/claim',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./pages/artist-claim-wizard.page').then((m) => m.ArtistClaimWizardPage),
    title: 'artistSpace.claim.title',
  },
  {
    path: 'artist-invitations/:token/accept',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./pages/artist-invite-accept.page').then((m) => m.ArtistInviteAcceptPage),
    title: 'artistSpace.inviteAccept.title',
  },
  {
    path: 'platform-ops/artist-requests',
    canActivate: [authGuard, platformAdminGuard],
    loadComponent: () =>
      import('./pages/platform-artist-requests.page').then(
        (m) => m.PlatformArtistRequestsPage,
      ),
    title: 'artistSpace.platform.title',
  },
];
