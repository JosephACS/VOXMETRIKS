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
    path: 'artist-space/music',
    canActivate: [
      authGuard,
      artistRequiredGuard,
      artistPermissionGuard('artist_space.catalog.view'),
    ],
    loadComponent: () =>
      import('./pages/artist-space-music.page').then((m) => m.ArtistSpaceMusicPage),
    title: 'artistSpace.music.title',
  },
  {
    path: 'artist-space/releases/new',
    canActivate: [
      authGuard,
      artistRequiredGuard,
      artistPermissionGuard('artist_space.release.create'),
    ],
    data: { releaseContext: 'artist' },
    loadComponent: () =>
      import('../catalog-publishing/pages/artist-release-wizard.page').then(
        (m) => m.ArtistReleaseWizardPage,
      ),
    title: 'publishing.wizard.title',
  },
  // Legacy split surfaces now live inside the single Music page (051).
  {
    path: 'artist-space/tracks',
    pathMatch: 'full',
    redirectTo: 'artist-space/music',
  },
  {
    path: 'artist-space/releases',
    pathMatch: 'full',
    redirectTo: 'artist-space/music',
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
    path: 'artist-invitations/accept',
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
